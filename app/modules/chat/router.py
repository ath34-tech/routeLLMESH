from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db

from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
)

from app.modules.chat.service import (
    ChatService,
)

from app.modules.chat.factory import (
    get_chat_service,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/completions",
    response_model=ChatResponse,
)
async def chat_completion(
    request: ChatRequest,
    service: ChatService = Depends(
        get_chat_service,
    ),
):

    return await service.chat(
        request,
    )