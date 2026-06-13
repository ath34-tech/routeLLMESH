from fastapi import HTTPException

from app.core.redis.keys import RedisKeys
from app.core.redis.repository import RedisRepository

from app.modules.model_vault.provider.repository import ProviderRepository

from .repository import ModelRepository
from .schemas import ModelCreate
from .schemas import ModelUpdate


class ModelService:

    def __init__(
        self,
        model_repository: ModelRepository,
        provider_repository: ProviderRepository,
    ):

        self.model_repository = model_repository
        self.provider_repository = provider_repository
        self.redis = RedisRepository()

    async def create(
        self,
        model: ModelCreate,
    ):

        provider = await self.provider_repository.get_by_id(
            model.provider_id
        )

        if provider is None:

            raise HTTPException(
                status_code=404,
                detail="Provider not found.",
            )

        existing = await self.model_repository.get_by_name(
            model.model_name
        )

        if existing:

            raise HTTPException(
                status_code=409,
                detail="Model already exists.",
            )

        entity = await self.model_repository.create(
            model
        )

        await self.redis.set_json(
            RedisKeys.model(entity.model_name),
            {
                "id": entity.id,
                "provider_id": entity.provider_id,
                "model_name": entity.model_name,
                "display_name": entity.display_name,
                "context_window": entity.context_window,
                "input_cost": entity.input_cost,
                "output_cost": entity.output_cost,
                "priority": entity.priority,
                "fallback_order": entity.fallback_order,
                "supports_stream": entity.supports_stream,
                "supports_tools": entity.supports_tools,
                "supports_vision": entity.supports_vision,
                "supports_reasoning": entity.supports_reasoning,
                "enabled": entity.enabled,
            },
        )

        return entity

    async def get_all(self):

        return await self.model_repository.get_all()

    async def get_by_id(
        self,
        model_id: int,
    ):

        model = await self.model_repository.get_by_id(
            model_id
        )

        if model is None:

            raise HTTPException(
                status_code=404,
                detail="Model not found.",
            )

        return model

    async def update(
        self,
        model_id: int,
        data: ModelUpdate,
    ):

        model = await self.model_repository.get_by_id(
            model_id
        )

        if model is None:

            raise HTTPException(
                status_code=404,
                detail="Model not found.",
            )

        updated = await self.model_repository.update(
            model,
            data,
        )

        await self.redis.set_json(
            RedisKeys.model(updated.model_name),
            {
                "id": updated.id,
                "provider_id": updated.provider_id,
                "model_name": updated.model_name,
                "display_name": updated.display_name,
                "context_window": updated.context_window,
                "input_cost": updated.input_cost,
                "output_cost": updated.output_cost,
                "priority": updated.priority,
                "fallback_order": updated.fallback_order,
                "supports_stream": updated.supports_stream,
                "supports_tools": updated.supports_tools,
                "supports_vision": updated.supports_vision,
                "supports_reasoning": updated.supports_reasoning,
                "enabled": updated.enabled,
            },
        )

        return updated

    async def delete(
        self,
        model_id: int,
    ):

        model = await self.model_repository.get_by_id(
            model_id
        )

        if model is None:

            raise HTTPException(
                status_code=404,
                detail="Model not found.",
            )

        await self.model_repository.delete(
            model
        )

        await self.redis.delete(
            RedisKeys.model(model.model_name)
        )

        return {
            "message": "Model deleted successfully."
        }