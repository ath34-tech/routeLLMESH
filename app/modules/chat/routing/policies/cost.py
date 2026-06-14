
from typing import List

from app.modules.chat.routing.policies.base import (
    Router,
    RankedCandidate,
    RoutingResult,
)
from app.modules.chat.schemas import ChatRequest


class CostRouter(Router):
    """
    Cost-first routing strategy.

    Ranks all enabled models by estimated cost.
    The cheapest model becomes the first candidate,
    while the remaining models serve as automatic fallbacks.
    """

    def __init__(self, redis_repo):
        self.redis = redis_repo

    async def route(
        self,
        request: ChatRequest,
        enabled_models: List[dict],
    ) -> RoutingResult:

        input_tokens = request.estimate_tokens()
        output_tokens = 500  # conservative estimate

        candidates: list[RankedCandidate] = []

        for model in enabled_models:

            model_name = model["model_name"]

            input_cost = model.get("input_cost", 0.0)
            output_cost = model.get("output_cost", 0.0)
            priority = model.get("priority", 50)

            total_cost = (
                input_tokens * input_cost
                + output_tokens * output_cost
            )

            # Lower cost is better.
            # Higher priority acts as a small tie-breaker.
            score = -(total_cost) + (priority * 0.001)

            candidates.append(
                RankedCandidate(
                    model_name=model_name,
                    score=score,
                    reasoning=(
                        f"Estimated cost=${total_cost:.6f}, "
                        f"priority={priority}"
                    ),
                    estimated_cost=total_cost,
                )
            )

        # Highest score first
        candidates.sort(
            key=lambda candidate: candidate.score,
            reverse=True,
        )

        return RoutingResult(
            candidate_models=candidates,
            routing_policy="cost",
            reasoning="Ranked models by estimated execution cost.",
            estimated_cost=(
                candidates[0].estimated_cost
                if candidates
                else None
            ),
        )

    async def observe_outcome(self, result: dict) -> None:
        """
        Cost router is deterministic and does not learn.
        """
        return
