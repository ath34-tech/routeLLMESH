from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List
from datetime import datetime

@dataclass
class RoutingResult:
    """
    Return type for all routing decisions.
    Immutable and observable.
    """
    selected_model: str
    routing_policy: str
    reasoning: str
    
    # Observability
    complexity_score: float | None = None
    estimated_cost: float | None = None
    all_candidates: Dict[str, float] | None = None
    context: Dict[str, Any] | None = None
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
            "selected_model": self.selected_model,
            "routing_policy": self.routing_policy,
            "reasoning": self.reasoning,
            "complexity_score": self.complexity_score,
            "estimated_cost": self.estimated_cost,
            "all_candidates": self.all_candidates,
            "context": self.context,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

class Router(ABC):
    """
    Abstract base for all routing policies.
    Implement this interface to add new routers.
    """
    
    @abstractmethod
    async def route(self, request, enabled_models: List[dict]) -> RoutingResult:
        """
        Select optimal model for request.
        
        Args:
            request: ChatRequest from user
            enabled_models: List of available models from Redis
        
        Returns:
            RoutingResult with selected model and metadata
        """
        pass
    
    @abstractmethod
    async def observe_outcome(self, result: Dict[str, Any]) -> None:
        """
        Learn from actual outcomes.
        Called after request completes.
        
        Args:
            result: {
                request_id: str,
                selected_model: str,
                user_satisfaction: bool,
                latency_ms: int,
                complexity_score: float (if applicable),
                ...
            }
        """
        pass