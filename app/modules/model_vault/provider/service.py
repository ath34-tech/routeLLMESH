from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import ProviderRepository
from .schemas import ProviderCreate
from .schemas import ProviderUpdate


class ProviderService:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.repository = ProviderRepository(db)

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

        return await self.repository.create(
            provider
        )

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

        return await self.repository.update(
            provider,
            data,
        )

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

        return {
            "message": "Provider deleted successfully."
        }
