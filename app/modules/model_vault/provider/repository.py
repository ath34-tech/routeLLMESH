from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .entity import Provider
from .schemas import ProviderCreate
from .schemas import ProviderUpdate


class ProviderRepository:

    def __init__(self, db: AsyncSession):

        self.db = db

    async def create(
        self,
        provider: ProviderCreate,
    ) -> Provider:

        entity = Provider(
            **provider.model_dump()
        )

        self.db.add(entity)

        await self.db.commit()

        await self.db.refresh(entity)

        return entity

    async def get_by_id(
        self,
        provider_id: int,
    ) -> Provider | None:

        result = await self.db.execute(
            select(Provider).where(
                Provider.id == provider_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
    ) -> Provider | None:

        result = await self.db.execute(
            select(Provider).where(
                Provider.name == name
            )
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
    ) -> list[Provider]:

        result = await self.db.execute(
            select(Provider)
        )

        return result.scalars().all()

    async def update(
        self,
        provider: Provider,
        data: ProviderUpdate,
    ) -> Provider:

        update_data = data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():

            setattr(
                provider,
                key,
                value,
            )

        await self.db.commit()

        await self.db.refresh(provider)

        return provider

    async def delete(
        self,
        provider: Provider,
    ) -> None:

        await self.db.delete(provider)

        await self.db.commit()
