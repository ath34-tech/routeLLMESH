
from fastapi import HTTPException

from app.core.redis.keys import RedisKeys
from app.core.redis.repository import RedisRepository

from app.modules.chat.schemas import ChatRequest

from app.modules.model_vault.model.repository import (
    ModelRepository,
)

from app.modules.model_vault.provider.repository import (
    ProviderRepository,
)

from app.modules.chat.provider_factory import (
    ProviderFactory,
)

from app.modules.chat.normalizer import (
    ResponseNormalizer,
)


class ChatService:

    def __init__(
        self,
        model_repository: ModelRepository,
        provider_repository: ProviderRepository,
    ):

        self.model_repository = model_repository
        self.provider_repository = provider_repository
        self.redis = RedisRepository()

    async def chat(
        self,
        request: ChatRequest,
    ):

        # -----------------------------
        # Step 1: Get model from Redis
        # -----------------------------

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

        # -----------------------------
        # Step 2: Get provider from Redis
        # -----------------------------

        provider = await self.redis.get_json(
            RedisKeys.provider(
                model["provider_id"]
            )
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
                RedisKeys.provider(
                    db_provider.id
                ),
                provider,
            )

        # -----------------------------
        # Step 3: Adapter
        # -----------------------------

        adapter = ProviderFactory.get_adapter(
            provider["adapter"]
        )

        # -----------------------------
        # Step 4: Execute
        # -----------------------------

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

        # -----------------------------
        # Step 5: Normalize
        # -----------------------------

        return ResponseNormalizer.normalize(
            response
        )
