from app.modules.chat.schemas import (
    ChatResponse,
)


class ResponseNormalizer:

    @staticmethod
    def normalize(
        response: dict,
    ) -> ChatResponse:

        return ChatResponse.model_validate(
            response
        )