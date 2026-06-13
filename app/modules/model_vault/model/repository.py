from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .entity import Model
from .schemas import ModelCreate
from .schemas import ModelUpdate


class ModelRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):

        self.db = db

    async def create(
        self,
        model: ModelCreate,
    ) -> Model:

        entity = Model(
            **model.model_dump()
        )

        self.db.add(entity)

        await self.db.commit()

        await self.db.refresh(entity)

        return entity

    async def get_by_id(
        self,
        model_id: int,
    ) -> Model | None:

        result = await self.db.execute(
            select(Model).where(
                Model.id == model_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        model_name: str,
    ) -> Model | None:

        result = await self.db.execute(
            select(Model).where(
                Model.model_name == model_name
            )
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
    ) -> list[Model]:

        result = await self.db.execute(
            select(Model)
        )

        return result.scalars().all()

    async def update(
        self,
        model: Model,
        data: ModelUpdate,
    ) -> Model:

        update_data = data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():

            setattr(
                model,
                key,
                value,
            )

        await self.db.commit()

        await self.db.refresh(model)

        return model

    async def delete(
        self,
        model: Model,
    ) -> None:

        await self.db.delete(model)

        await self.db.commit()

    async def get_enabled_by_name(
        self,
        model_name: str,
    ) -> Model | None:

        result = await self.db.execute(
            select(Model).where(
                Model.model_name == model_name,
                Model.enabled == True,
            )
        )

        return result.scalar_one_or_none()