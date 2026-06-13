from fastapi import HTTPException
from typing import Optional
from app.modules.chat.schemas import ChatRequest
from app.modules.chat.routing.registry import RouterRegistry
from app.modules.chat.routing.telemetry import RoutingTelemetry, RoutingOutcome
from app.core.redis.repository import RedisRepository
import logging

logger = logging.getLogger(__name__)

class RoutingEngine:
    """
    Routing orchestrator adapted to your Redis structure.
    
    Your Redis:
    - model:{model_name} → JSON metadata
    - provider:name:{provider_name} → provider data
    - No pre-made enabled models set
    """
    
    _instance = None
    _registry: Optional[RouterRegistry] = None
    _telemetry: Optional[RoutingTelemetry] = None
    _redis: Optional[RedisRepository] = None
    
    @classmethod
    def initialize(cls, redis_repo: RedisRepository):
        """One-time initialization. Call from FastAPI startup."""
        cls._redis = redis_repo
        cls._registry = RouterRegistry(redis_repo)
        cls._telemetry = RoutingTelemetry(redis_repo)
    
    @staticmethod
    async def route(request: ChatRequest) -> str:
        """
        Route request to optimal model.
        """
        
        if RoutingEngine._registry is None:
            raise RuntimeError(
                "RoutingEngine not initialized. Call initialize() in startup."
            )
        
        # If model specified, return it unchanged
        if request.model != "auto":
            return request.model
        
        # Get routing policy
        routing_policy = request.routing_policy or "complexity"
        
        if routing_policy not in RoutingEngine._registry.list_policies():
            raise ValueError(
                f"Routing policy '{routing_policy}' not supported. "
                f"Available: {RoutingEngine._registry.list_policies()}"
            )
        
        # Load enabled models
        enabled_models = await RoutingEngine._load_enabled_models()
        
        if not enabled_models:
            raise HTTPException(
                status_code=503,
                detail="No enabled models available."
            )
        
        # Get router and route
        router = RoutingEngine._registry.get(routing_policy)
        result = await router.route(request, enabled_models)
        
        # Log routing decision
        logger.info(
            f"routing_decision",
            extra={
                "routing_policy": routing_policy,
                "selected_model": result.selected_model,
                "complexity_score": result.complexity_score,
                "reasoning": result.reasoning,
            }
        )
        
        # Store routing result for outcome tracking
        if hasattr(request, 'id') and request.id:
            await RoutingEngine._redis.set_json(
                f"routing:decision:{request.id}",
                result.to_dict(),  # ✅ FIXED: Use to_dict() instead of __dict__
                ttl=3600
            )
        
        return result.selected_model
    
    @staticmethod
    async def observe_outcome(request_id: str, outcome: RoutingOutcome) -> None:
        """
        Called after request completes to update router state.
        """
        
        # Get original routing decision
        decision = await RoutingEngine._redis.get_json(
            f"routing:decision:{request_id}"
        )
        
        if decision:
            outcome.routing_policy = decision.get("routing_policy")
            outcome.complexity_score = decision.get("complexity_score")
        
        # Let router learn from outcome
        router = RoutingEngine._registry.get(outcome.routing_policy)
        await router.observe_outcome(outcome.to_dict())  # ✅ FIXED: Use to_dict()
        
        # Log telemetry
        await RoutingEngine._telemetry.log_outcome(outcome)
    
    @staticmethod
    async def _load_enabled_models() -> list:
        """
        Load all enabled models from Redis.
        
        Your Redis structure: model:{model_name} → JSON
        Uses SCAN to find all model keys.
        """
        
        enabled_models = []
        cursor = 0
        
        # SCAN for all model:* keys
        while True:
            cursor, keys = await RoutingEngine._redis.scan(
                cursor=cursor,
                match="model:*",
                count=100
            )
            
            # Fetch each model
            for key in keys:
                model = await RoutingEngine._redis.get_json(key)
                
                # Only include enabled models
                if model and model.get("enabled", True):
                    enabled_models.append(model)
            
            # Break if cursor back to 0 (full scan complete)
            if cursor == 0:
                break
        
        return enabled_models