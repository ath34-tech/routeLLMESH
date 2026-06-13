
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis.keys import RedisKeys
from app.core.redis.repository import RedisRepository

from .repository import ProviderRepository
from .schemas import ProviderCreate
from .schemas import ProviderUpdate


class ProviderService:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.repository = ProviderRepository(db)
        self.redis = RedisRepository()

    async def create(
        self,
        provider: ProviderCreate,
    ):

        existing = await self.repository.get_by_name(
            provider.name
        )

        if existing:

            raise HTTPException(
                status_code=409,
                detail="Provider already exists.",
            )

        entity = await self.repository.create(
            provider
        )

        await self.redis.set_json(
            RedisKeys.provider(entity.id),
            {
                "id": entity.id,
                "name": entity.name,
                "api_key": entity.api_key,
                "base_url": entity.base_url,
                "adapter": entity.adapter,
                "enabled": entity.enabled,
            },
        )

        return entity

    async def get_by_id(
        self,
        provider_id: int,
    ):

        provider = await self.repository.get_by_id(
            provider_id
        )

        if provider is None:

            raise HTTPException(
                status_code=404,
                detail="Provider not found.",
            )

        return provider

    async def get_all(self):

        return await self.repository.get_all()

    async def update(
        self,
        provider_id: int,
        data: ProviderUpdate,
    ):

        provider = await self.repository.get_by_id(
            provider_id
        )

        if provider is None:

            raise HTTPException(
                status_code=404,
                detail="Provider not found.",
            )

        updated = await self.repository.update(
            provider,
            data,
        )

        await self.redis.set_json(
            RedisKeys.provider(updated.id),
            {
                "id": updated.id,
                "name": updated.name,
                "api_key": updated.api_key,
                "base_url": updated.base_url,
                "adapter": updated.adapter,
                "enabled": updated.enabled,
            },
        )

        return updated

    async def delete(
        self,
        provider_id: int,
    ):

        provider = await self.repository.get_by_id(
            provider_id
        )

        if provider is None:

            raise HTTPException(
                status_code=404,
                detail="Provider not found.",
            )

        await self.repository.delete(
            provider
        )

        await self.redis.delete(
            RedisKeys.provider(provider.id)
        )

        return {
            "message": "Provider deleted successfully."
        }
