
from fastapi import HTTPException
from typing import Optional

from app.modules.chat.schemas import ChatRequest
from app.modules.chat.routing.registry import RouterRegistry
from app.modules.chat.routing.telemetry import (
    RoutingTelemetry,
    RoutingOutcome,
)
from app.modules.chat.routing.policies.base import RoutingResult
from app.core.redis.repository import RedisRepository
from app.core.redis.keys import RedisKeys

import logging

logger = logging.getLogger(__name__)


class RoutingEngine:
    """
    Central routing orchestrator.

    Responsibilities:

    - load enabled model pool
    - select routing strategy
    - execute routing policy
    - return ranked execution plan
    """

    _registry: Optional[RouterRegistry] = None
    _telemetry: Optional[RoutingTelemetry] = None
    _redis: Optional[RedisRepository] = None

    @classmethod
    def initialize(
        cls,
        redis_repo: RedisRepository,
    ):

        cls._redis = redis_repo
        cls._registry = RouterRegistry(redis_repo)
        cls._telemetry = RoutingTelemetry(redis_repo)

    @staticmethod
    async def route(
        request: ChatRequest,
    ) -> RoutingResult:

        if RoutingEngine._registry is None:
            raise RuntimeError(
                "RoutingEngine not initialized."
            )

        # -------------------------
        # Manual model selection
        # -------------------------

        if request.model != "auto":

            return RoutingResult.manual(
                model_name=request.model
            )

        # -------------------------
        # Policy
        # -------------------------

        routing_policy = (
            request.routing_policy
            or "complexity"
        )

        if (
            routing_policy
            not in RoutingEngine._registry.list_policies()
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported routing policy: "
                    f"{routing_policy}"
                ),
            )

        # -------------------------
        # Load model pool
        # -------------------------

        enabled_models = await RoutingEngine._load_enabled_models()

        if not enabled_models:

            raise HTTPException(
                status_code=503,
                detail="No enabled models available.",
            )

        # -------------------------
        # Route
        # -------------------------

        router = RoutingEngine._registry.get(
            routing_policy
        )

        result = await router.route(
            request=request,
            enabled_models=enabled_models,
        )

        # -------------------------
        # Logging
        # -------------------------

        logger.info(
            "\n"
            "Requested Model : auto\n"
            "Policy          : %s\n"
            "Complexity      : %s\n"
            "Candidates      : %s",
            routing_policy,
            result.complexity_score,
            [
                c.model_name
                for c in result.candidate_models
            ],
        )

        # -------------------------
        # Store decision
        # -------------------------

        if getattr(request, "id", None):

            await RoutingEngine._redis.set_json(
                f"routing:decision:{request.id}",
                result.to_dict(),
                ttl=3600,
            )

        return result

    @staticmethod
    async def observe_outcome(
        request_id: str,
        outcome: RoutingOutcome,
    ) -> None:

        decision = (
            await RoutingEngine._redis.get_json(
                f"routing:decision:{request_id}"
            )
        )

        if decision:

            outcome.routing_policy = decision.get(
                "routing_policy"
            )

            outcome.complexity_score = decision.get(
                "complexity_score"
            )

        router = RoutingEngine._registry.get(
            outcome.routing_policy
        )

        await router.observe_outcome(
            outcome.to_dict()
        )

        await RoutingEngine._telemetry.log_outcome(
            outcome
        )


    @staticmethod
    async def _load_enabled_models() -> list:
        """
        Load all enabled models from Redis.
        Temporary implementation using SCAN.
        """

        enabled_models = []

        cursor = 0

        while True:

            cursor, keys = await RoutingEngine._redis.scan(
                cursor=cursor,
                match="model:*",
                count=100,
            )

            for key in keys:

                model = await RoutingEngine._redis.get_json(key)

                if model and model.get("enabled", True):
                    enabled_models.append(model)

            if cursor == 0:
                break

        return enabled_models
