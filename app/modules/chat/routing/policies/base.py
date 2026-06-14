from abc import ABC, abstractmethod
from dataclasses import dataclass,field
from typing import Any, Dict, List
from datetime import datetime



@dataclass
class RankedCandidate:
    """
    Represents a single candidate model in the routing ranking.
    """

    model_name: str
    score: float
    reasoning: str
    estimated_cost: float | None = None


@dataclass
class RoutingResult:
    """
    Return type for all routing decisions.

    Contains an ordered list of candidate models.
    The first model is the preferred choice.
    Remaining models are automatic fallbacks.
    """

    candidate_models: List[RankedCandidate]

    routing_policy: str

    reasoning: str

    # Observability
    complexity_score: float | None = None

    context: Dict[str, Any] | None = None
    estimated_cost: float | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def selected_model(self) -> str | None:
        """
        Backward compatibility.

        Returns the highest-ranked candidate.
        """

        if not self.candidate_models:
            return None

        return self.candidate_models[0].model_name

    def to_dict(self) -> dict:
        """
        Convert to JSON-serializable dict.
        """

        return {
            "selected_model": self.selected_model,
            "candidate_models": [
                {
                    "model_name": candidate.model_name,
                    "score": candidate.score,
                    "reasoning": candidate.reasoning,
                    "estimated_cost": candidate.estimated_cost,
                }
                for candidate in self.candidate_models
            ],
            "routing_policy": self.routing_policy,
            "reasoning": self.reasoning,
            "complexity_score": self.complexity_score,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


    @classmethod
    def manual(cls, model_name: str):
        """
        Create a RoutingResult for explicit user-selected models.

        No routing is performed.
        """

        return cls(
            candidate_models=[
                RankedCandidate(
                    model_name=model_name,
                    score=float("inf"),
                    reasoning="Manual model selection",
                    estimated_cost=None,
                )
            ],
            routing_policy="manual",
            reasoning="User explicitly selected a model.",
            complexity_score=None,
            estimated_cost=None,
            context=None,
        )



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