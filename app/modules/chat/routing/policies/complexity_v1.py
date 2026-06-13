
from typing import Dict, Any, List

from app.modules.chat.routing.analyzer import ComplexityAnalyzer
from app.modules.chat.routing.policies.base import (
    Router,
    RoutingResult,
)
from app.core.redis.keys import RedisKeys


class ComplexityRouter(Router):

    def __init__(
        self,
        redis_repo,
    ):
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
        # Load model pool from Redis
        # ------------------------

        if enabled_models is None:

            enabled_models = await self.redis.get_json(
                RedisKeys.enabled_models()
            )

        if not enabled_models:

            raise Exception(
                "No enabled models found."
            )

        # ------------------------
        # Score every model
        # ------------------------

        ranking = {}

        for model in enabled_models:

            if not model.get(
                "enabled",
                False,
            ):
                continue

            score = self._score(
                model=model,
                complexity=complexity,
                request=request,
            )

            ranking[
                model["model_name"]
            ] = score

        # ------------------------
        # Pick winner
        # ------------------------

        winner = max(
            enabled_models,
            key=lambda m: ranking.get(
                m["model_name"],
                float("-inf"),
            ),
        )

        return RoutingResult(
            selected_model=winner["model_name"],
            routing_policy="complexity",
            complexity_score=complexity,
            estimated_cost=winner["input_cost"],
            reasoning=(
                f"Complexity={complexity:.1f}. "
                f"Selected highest scoring model."
            ),
            all_candidates=ranking,
            context={
                "analysis": analysis,
                "winner_score": ranking[
                    winner["model_name"]
                ],
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
        # priority
        # ------------------

        score += model.get(
            "priority",
            0,
        )

        # ------------------
        # reasoning
        # ------------------

        if complexity >= 7:

            if model.get(
                "supports_reasoning",
                False,
            ):

                score += 100

            else:

                score -= 1000

        # ------------------
        # context window
        # ------------------

        score += (
            model.get(
                "context_window",
                4096,
            )
            / 10000
        )

        # ------------------
        # dynamic cost weight
        # ------------------

        if complexity <= 2:

            cost_weight = 40

        elif complexity <= 5:

            cost_weight = 15

        else:

            cost_weight = 2

        score -= (
            model.get(
                "input_cost",
                0,
            )
            * cost_weight
        )

        score -= (
            model.get(
                "output_cost",
                0,
            )
            * cost_weight
        )

        # ------------------
        # tools
        # ------------------

        if request.tools:

            if model.get(
                "supports_tools",
                False,
            ):

                score += 30

            else:

                score -= 500

        # ------------------
        # estimated token bonus
        # ------------------

        estimated_tokens = len(
            " ".join(
                m.content
                for m in request.messages
            ).split()
        ) * 1.5

        if model.get(
            "context_window",
            4096,
        ) > estimated_tokens * 2:

            score += 10

        return score
