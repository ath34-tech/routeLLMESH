
from fastapi import APIRouter
from fastapi import Depends

from fastapi.responses import StreamingResponse

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
)
async def chat_completion(
    request: ChatRequest,
    service: ChatService = Depends(
        get_chat_service,
    ),
):

    result = await service.chat(
        request,
    )

    if request.stream:

        return StreamingResponse(
            result,
            media_type="text/event-stream",
        )

    return result
