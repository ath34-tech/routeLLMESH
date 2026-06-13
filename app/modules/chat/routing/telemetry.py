# Same as before
from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class RoutingOutcome:
    """
    Outcome event after request completion.
    Logged for learning and analytics.
    """
    request_id: str
    selected_model: str
    routing_policy: str
    user_satisfaction: bool
    latency_ms: int
    cost_usd: float
    complexity_score: float | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """
        Convert to JSON-serializable dict.
        Converts datetime to ISO format string.
        """
        return {
            "request_id": self.request_id,
            "selected_model": self.selected_model,
            "routing_policy": self.routing_policy,
            "user_satisfaction": self.user_satisfaction,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "complexity_score": self.complexity_score,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class RoutingTelemetry:
    """
    Collect and log routing outcomes.
    """
    
    def __init__(self, redis_repo):
        self.redis = redis_repo
    
    async def log_outcome(self, outcome: RoutingOutcome) -> None:
        """Log routing outcome for learning."""
        
        logger.info(
            f"routing_outcome",
            extra={
                "request_id": outcome.request_id,
                "selected_model": outcome.selected_model,
                "routing_policy": outcome.routing_policy,
                "user_satisfaction": outcome.user_satisfaction,
                "latency_ms": outcome.latency_ms,
                "cost_usd": outcome.cost_usd,
                "complexity_score": outcome.complexity_score,
            }
        )
        
        # Store in Redis using to_dict()
        key = f"routing:outcomes:{outcome.request_id}"
        await self.redis.set_json(
            key,
            outcome.to_dict(),  # ✅ FIXED: Use to_dict()
            ttl=86400
        )