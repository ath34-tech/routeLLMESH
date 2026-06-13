
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db

from .schemas import ProviderCreate
from .schemas import ProviderUpdate
from .schemas import ProviderResponse
from .service import ProviderService


router = APIRouter(
    prefix="/providers",
    tags=["Providers"],
)


@router.post(
    "/",
    response_model=ProviderResponse,
    status_code=201,
)
async def create_provider(
    provider: ProviderCreate,
    db: AsyncSession = Depends(get_db),
):

    service = ProviderService(db)

    return await service.create(provider)


@router.get(
    "/",
    response_model=list[ProviderResponse],
)
async def get_all_providers(
    db: AsyncSession = Depends(get_db),
):

    service = ProviderService(db)

    return await service.get_all()


@router.get(
    "/{provider_id}",
    response_model=ProviderResponse,
)
async def get_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
):

    service = ProviderService(db)

    return await service.get_by_id(provider_id)


@router.put(
    "/{provider_id}",
    response_model=ProviderResponse,
)
async def update_provider(
    provider_id: int,
    provider: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
):

    service = ProviderService(db)

    return await service.update(
        provider_id,
        provider,
    )


@router.delete(
    "/{provider_id}",
)
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
):

    service = ProviderService(db)

    return await service.delete(provider_id)
