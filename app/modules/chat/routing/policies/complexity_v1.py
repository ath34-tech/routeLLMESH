
from typing import Dict, Any, List

from app.modules.chat.routing.analyzer import ComplexityAnalyzer
from app.modules.chat.routing.policies.base import (
    Router,
    RoutingResult,
    RankedCandidate,
)
from app.core.redis.keys import RedisKeys


class ComplexityRouter(Router):

    def __init__(self, redis_repo):
        self.redis = redis_repo
        self.analyzer = ComplexityAnalyzer()

    async def route(
        self,
        request,
        enabled_models: List[dict] | None = None,
    ) -> RoutingResult:

        # ------------------------
        # Analyze prompt
        # ------------------------

        analysis = self.analyzer.analyze(request)
        complexity = analysis["score"]

        # ------------------------
        # Load model pool
        # ------------------------

        if enabled_models is None:

            enabled_models = await self.redis.get_json(
                RedisKeys.enabled_models()
            )

        if not enabled_models:

            raise Exception("No enabled models found.")

        # ------------------------
        # Score every model
        # ------------------------

        candidates: list[RankedCandidate] = []

        for model in enabled_models:

            if not model.get("enabled", False):
                continue

            score = self._score(
                model=model,
                complexity=complexity,
                request=request,
            )

            candidates.append(
                RankedCandidate(
                    model_name=model["model_name"],
                    score=score,
                    reasoning=(
                        f"Complexity={complexity:.1f}, "
                        f"priority={model.get('priority',0)}"
                    ),
                    estimated_cost=(
                        model.get("input_cost", 0)
                        + model.get("output_cost", 0)
                    ),
                )
            )

        if not candidates:
            raise Exception("No eligible models found.")

        # ------------------------
        # Rank candidates
        # ------------------------

        candidates.sort(
            key=lambda candidate: candidate.score,
            reverse=True,
        )

        # ------------------------
        # Build result
        # ------------------------

        return RoutingResult(
            candidate_models=candidates,
            routing_policy="complexity",
            complexity_score=complexity,
            estimated_cost=candidates[0].estimated_cost,
            reasoning=(
                f"Prompt complexity={complexity:.1f}. "
                "Models ranked by routing score."
            ),
            context={
                "analysis": analysis,
                "winner_score": candidates[0].score,
            },
        )

    async def observe_outcome(
        self,
        result: Dict[str, Any],
    ) -> None:

        # deterministic router

        return

    @staticmethod
    def _score(
        model,
        complexity,
        request,
    ) -> float:

        score = 0.0

        # ------------------
        # Priority
        # ------------------

        score += model.get("priority", 0)

        # ------------------
        # Reasoning capability
        # ------------------

        if complexity >= 7:

            if model.get("supports_reasoning", False):
                score += 100
            else:
                score -= 1000

        # ------------------
        # Context window
        # ------------------

        score += (
            model.get("context_window", 4096)
            / 10000
        )

        # ------------------
        # Dynamic cost penalty
        # ------------------

        if complexity <= 2:
            cost_weight = 40
        elif complexity <= 5:
            cost_weight = 15
        else:
            cost_weight = 2

        score -= (
            model.get("input_cost", 0)
            * cost_weight
        )

        score -= (
            model.get("output_cost", 0)
            * cost_weight
        )

        # ------------------
        # Tool support
        # ------------------

        if getattr(request, "tools", None):

            if model.get("supports_tools", False):
                score += 30
            else:
                score -= 500

        # ------------------
        # Context fit bonus
        # ------------------

        estimated_tokens = (
            len(
                " ".join(
                    m.content
                    for m in request.messages
                ).split()
            )
            * 1.5
        )

        if (
            model.get("context_window", 4096)
            >= estimated_tokens * 2
        ):
            score += 10

        return score
