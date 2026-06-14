
import numpy as np
from typing import Any, Dict, List

from app.modules.chat.routing.analyzer import ComplexityAnalyzer
from app.modules.chat.routing.policies.base import (
    Router,
    RankedCandidate,
    RoutingResult,
)


class ComplexityThompsonRouter(Router):
    """
    Thompson Sampling complexity router.

    Returns a ranked candidate list instead of a single model.
    """

    def __init__(self, redis_repo):
        self.redis = redis_repo
        self.analyzer = ComplexityAnalyzer()

    async def route(
        self,
        request,
        enabled_models: List[dict],
    ) -> RoutingResult:

        analysis = self.analyzer.analyze(request)

        complexity_score = analysis["score"]
        complexity_level = int(complexity_score)

        candidates: list[RankedCandidate] = []

        for model in enabled_models:

            if not model.get("enabled", False):
                continue

            model_name = model["model_name"]

            alpha_key = (
                f"routing:thompson:{model_name}:"
                f"complexity_{complexity_level}:alpha"
            )

            beta_key = (
                f"routing:thompson:{model_name}:"
                f"complexity_{complexity_level}:beta"
            )

            alpha = float(
                await self.redis.get(alpha_key) or "1"
            )

            beta = float(
                await self.redis.get(beta_key) or "1"
            )

            sample = np.random.beta(alpha, beta)

            # capability filtering

            if (
                complexity_score >= 7
                and not model.get(
                    "supports_reasoning",
                    False,
                )
            ):
                continue

            if (
                self._request_has_tools(request)
                and not model.get(
                    "supports_tools",
                    False,
                )
            ):
                continue

            if (
                self._request_needs_vision(request)
                and not model.get(
                    "supports_vision",
                    False,
                )
            ):
                continue

            candidates.append(
                RankedCandidate(
                    model_name=model_name,
                    score=sample,
                    reasoning=(
                        f"Thompson sample={sample:.4f} "
                        f"(α={alpha:.0f}, β={beta:.0f})"
                    ),
                    estimated_cost=(
                        model.get("input_cost", 0)
                        + model.get("output_cost", 0)
                    ),
                )
            )

        if not candidates:

            fallback = sorted(
                enabled_models,
                key=lambda m: m.get(
                    "priority",
                    0,
                ),
                reverse=True,
            )

            candidates = [
                RankedCandidate(
                    model_name=m["model_name"],
                    score=float(
                        m.get(
                            "priority",
                            0,
                        )
                    ),
                    reasoning="Priority fallback",
                    estimated_cost=(
                        m.get("input_cost", 0)
                        + m.get("output_cost", 0)
                    ),
                )
                for m in fallback
            ]

        candidates.sort(
            key=lambda candidate: candidate.score,
            reverse=True,
        )

        return RoutingResult(
            candidate_models=candidates,
            routing_policy="complexity",
            reasoning="Thompson Sampling routing",
            complexity_score=complexity_score,
            estimated_cost=(
                candidates[0].estimated_cost
                if candidates
                else None
            ),
            context={
                "analysis": analysis,
                "beliefs": {
                    candidate.model_name: candidate.reasoning
                    for candidate in candidates
                },
            },
        )

    async def observe_outcome(
        self,
        result: Dict[str, Any],
    ) -> None:

        model_name = result.get(
            "selected_model"
        )

        if not model_name:
            return

        complexity = int(
            result.get(
                "complexity_score",
                5,
            )
        )

        alpha_key = (
            f"routing:thompson:{model_name}:"
            f"complexity_{complexity}:alpha"
        )

        beta_key = (
            f"routing:thompson:{model_name}:"
            f"complexity_{complexity}:beta"
        )

        if result.get(
            "user_satisfaction",
            False,
        ):
            await self.redis.increment(
                alpha_key
            )
        else:
            await self.redis.increment(
                beta_key
            )

    @staticmethod
    def _request_has_tools(request):

        return bool(
            getattr(
                request,
                "tools",
                None,
            )
        )

    @staticmethod
    def _request_needs_vision(request):

        for msg in request.messages:

            content = getattr(
                msg,
                "content",
                None,
            )

            if isinstance(
                content,
                list,
            ):

                for item in content:

                    if (
                        isinstance(
                            item,
                            dict,
                        )
                        and item.get("type")
                        == "image_url"
                    ):
                        return True

        return False
