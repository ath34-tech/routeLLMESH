from fastapi import APIRouter

from app.modules.model_vault.provider.router import (
    router as provider_router,
)

from app.modules.model_vault.model.router import (
    router as model_router,
)
from app.modules.chat.router import router as chat_router


api_v1_router = APIRouter(
    prefix="/v1",
)

api_v1_router.include_router(
    provider_router
)

api_v1_router.include_router(
    model_router
)

api_v1_router.include_router(chat_router)