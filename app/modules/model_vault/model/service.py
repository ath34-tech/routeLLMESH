from fastapi import HTTPException

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

        return await self.model_repository.create(
            model
        )

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

        return await self.model_repository.update(
            model,
            data,
        )

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

        return {
            "message": "Model deleted successfully."
        }