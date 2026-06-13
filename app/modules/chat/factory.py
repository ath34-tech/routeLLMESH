from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db

from app.modules.model_vault.model.repository import (
    ModelRepository,
)

from app.modules.model_vault.provider.repository import (
    ProviderRepository,
)

from app.modules.chat.service import ChatService


def get_chat_service(
    db: AsyncSession = Depends(get_db),
) -> ChatService:

    model_repository = ModelRepository(db)

    provider_repository = ProviderRepository(db)

    return ChatService(
        model_repository=model_repository,
        provider_repository=provider_repository,
    )