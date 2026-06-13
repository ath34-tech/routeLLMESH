import time
from fastapi import HTTPException
from app.core.redis.keys import RedisKeys
from app.core.redis.repository import RedisRepository
from app.modules.chat.schemas import ChatRequest
from app.modules.model_vault.model.repository import ModelRepository
from app.modules.model_vault.provider.repository import ProviderRepository
from app.modules.chat.provider_factory import ProviderFactory
from app.modules.chat.normalizer import ResponseNormalizer
from app.modules.chat.routing import RoutingEngine, RoutingOutcome

class ChatService:

    def __init__(
        self,
        model_repository: ModelRepository,
        provider_repository: ProviderRepository,
    ):
        self.model_repository = model_repository
        self.provider_repository = provider_repository
        self.redis = RedisRepository()

    async def chat(self, request: ChatRequest):
        
        start_time = time.time()
        
        # ============================================
        # ROUTING: Get optimal model
        # ============================================
        
        selected_model = await RoutingEngine.route(request)
        request.model = selected_model
        
        # ============================================
        # Step 1: Get model from Redis
        # ============================================

        model = await self.redis.get_json(
            RedisKeys.model(request.model)
        )

        if model is None:
            db_model = await self.model_repository.get_enabled_by_name(
                request.model
            )

            if db_model is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Model '{request.model}' not found.",
                )

            model = {
                "id": db_model.id,
                "provider_id": db_model.provider_id,
                "model_name": db_model.model_name,
                "display_name": db_model.display_name,
                "context_window": db_model.context_window,
                "input_cost": db_model.input_cost,
                "output_cost": db_model.output_cost,
                "priority": db_model.priority,
                "fallback_order": db_model.fallback_order,
                "supports_stream": db_model.supports_stream,
                "supports_tools": db_model.supports_tools,
                "supports_vision": db_model.supports_vision,
                "supports_reasoning": db_model.supports_reasoning,
                "enabled": db_model.enabled,
            }

            await self.redis.set_json(
                RedisKeys.model(request.model),
                model,
            )

        # ============================================
        # Step 2: Get provider from Redis
        # ============================================

        provider = await self.redis.get_json(
            RedisKeys.provider(model["provider_id"])
        )

        if provider is None:
            db_provider = await self.provider_repository.get_by_id(
                model["provider_id"]
            )

            if db_provider is None:
                raise HTTPException(
                    status_code=404,
                    detail="Provider not found.",
                )

            provider = {
                "id": db_provider.id,
                "name": db_provider.name,
                "api_key": db_provider.api_key,
                "base_url": db_provider.base_url,
                "adapter": db_provider.adapter,
                "enabled": db_provider.enabled,
            }

            await self.redis.set_json(
                RedisKeys.provider(db_provider.id),
                provider,
            )

        # ============================================
        # Step 3: Get Adapter
        # ============================================

        adapter = ProviderFactory.get_adapter(provider["adapter"])

        # ============================================
        # Step 4: Execute (Stream or Non-stream)
        # ============================================

        try:
            if request.stream:
                return adapter.stream_chat(
                    provider=provider,
                    model=model,
                    request=request,
                )

            response = await adapter.chat(
                provider=provider,
                model=model,
                request=request,
            )

            # ============================================
            # Step 5: Normalize Response
            # ============================================

            normalized_response = ResponseNormalizer.normalize(response)
            
            # ============================================
            # OBSERVABILITY: Log routing outcome for learning
            # ============================================
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Calculate cost
            input_tokens = request.estimate_tokens()
            output_tokens = self._estimate_output_tokens(normalized_response)
            cost = (
                input_tokens * model["input_cost"] +
                output_tokens * model["output_cost"]
            )
            
            # Get complexity score from routing decision
            routing_decision = await self.redis.get_json(
                f"routing:decision:{request.id}"
            )
            complexity_score = (
                routing_decision.get("complexity_score")
                if routing_decision else 5.0
            )
            
            # Create outcome
            outcome = RoutingOutcome(
                request_id=request.id,
                selected_model=selected_model,
                routing_policy=request.routing_policy or "complexity",
                user_satisfaction=True,  # Could be from user feedback
                latency_ms=latency_ms,
                cost_usd=cost,
                complexity_score=complexity_score,
                tokens_input=input_tokens,
                tokens_output=output_tokens,
            )
            
            # Let routers learn from outcome (Thompson Sampling updates)
            await RoutingEngine.observe_outcome(request.id, outcome)
            
            return normalized_response

        except Exception as e:
            # Log failed request for observability
            latency_ms = int((time.time() - start_time) * 1000)
            
            outcome = RoutingOutcome(
                request_id=request.id,
                selected_model=selected_model,
                routing_policy=request.routing_policy or "complexity",
                user_satisfaction=False,  # Failed request
                latency_ms=latency_ms,
                cost_usd=0,
                complexity_score=5.0,
            )
            
            await RoutingEngine.observe_outcome(request.id, outcome)
            
            raise e
    
    @staticmethod
    def _estimate_output_tokens(response: dict) -> int:
        """Estimate output tokens from response."""
        try:
            # If response has usage info
            if "usage" in response:
                return response["usage"].get("completion_tokens", 500)
            
            # Fallback: estimate from content length
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return max(100, len(content) // 4)
        except:
            return 500