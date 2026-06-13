from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class Message(BaseModel):

    role: Literal[
        "system",
        "developer",
        "user",
        "assistant",
        "tool",
    ]

    content: Any

    name: str | None = None

    tool_call_id: str | None = None


class Tool(BaseModel):

    type: str

    function: dict


class ResponseFormat(BaseModel):

    type: Literal[
        "text",
        "json_object",
    ] = "text"


class ChatRequest(BaseModel):

    model: str = Field(
        ...,
        examples=["gpt-4o"],
    )

    messages: list[Message]

    temperature: float | None = 1.0

    top_p: float | None = 1.0

    max_completion_tokens: int | None = None

    stream: bool = False

    tools: list[Tool] | None = None

    tool_choice: str | dict | None = "auto"

    response_format: ResponseFormat | None = None

    stop: str | list[str] | None = None

    seed: int | None = None

    parameters: dict[str, Any] = {}


class ChatMessage(BaseModel):

    role: str

    content: Any


class Choice(BaseModel):

    index: int

    message: ChatMessage

    finish_reason: str | None = None


class Usage(BaseModel):

    prompt_tokens: int

    completion_tokens: int

    total_tokens: int


class ChatResponse(BaseModel):

    id: str

    object: str = "chat.completion"

    created: int

    model: str

    choices: list[Choice]

    usage: Usage