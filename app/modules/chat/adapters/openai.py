import httpx

from app.modules.chat.adapters.base import BaseAdapter
from app.modules.chat.schemas import ChatRequest


class OpenAIAdapter(BaseAdapter):

    async def chat(
        self,
        provider,
        model,
        request: ChatRequest,
    ):

        url = f"{provider.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model.model_name,
            "messages": [
                message.model_dump(
                    exclude_none=True
                )
                for message in request.messages
            ],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": request.stream,
            "tools": request.tools,
            "tool_choice": request.tool_choice,
            "response_format": (
                request.response_format.model_dump()
                if request.response_format
                else None
            ),
            "max_completion_tokens": request.max_completion_tokens,
            "stop": request.stop,
            "seed": request.seed,
        }

        payload = {
            key: value
            for key, value in payload.items()
            if value is not None
        }

        payload.update(
            request.parameters
        )

        async with httpx.AsyncClient(
            timeout=120,
        ) as client:

            response = await client.post(
                url=url,
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

        return response.json()