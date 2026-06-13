from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.model_vault.provider.repository import ProviderRepository

from .repository import ModelRepository
from .schemas import ModelCreate
from .schemas import ModelResponse
from .schemas import ModelUpdate
from .service import ModelService


router = APIRouter(
    prefix="/models",
    tags=["Models"],
)


def get_model_service(
    db: AsyncSession = Depends(get_db),
) -> ModelService:

    model_repository = ModelRepository(db)

    provider_repository = ProviderRepository(db)

    return ModelService(
        model_repository=model_repository,
        provider_repository=provider_repository,
    )


@router.post(
    "/",
    response_model=ModelResponse,
    status_code=201,
)
async def create_model(
    model: ModelCreate,
    service: ModelService = Depends(get_model_service),
):

    return await service.create(model)


@router.get(
    "/",
    response_model=list[ModelResponse],
)
async def get_all_models(
    service: ModelService = Depends(get_model_service),
):

    return await service.get_all()


@router.get(
    "/{model_id}",
    response_model=ModelResponse,
)
async def get_model(
    model_id: int,
    service: ModelService = Depends(get_model_service),
):

    return await service.get_by_id(model_id)


@router.put(
    "/{model_id}",
    response_model=ModelResponse,
)
async def update_model(
    model_id: int,
    model: ModelUpdate,
    service: ModelService = Depends(get_model_service),
):

    return await service.update(
        model_id,
        model,
    )


@router.delete(
    "/{model_id}",
)
async def delete_model(
    model_id: int,
    service: ModelService = Depends(get_model_service),
):

    return await service.delete(model_id)