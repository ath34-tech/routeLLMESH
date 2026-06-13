from typing import Any
from typing import Literal
import uuid

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

    # -------------------------
    # Request ID (for tracking)
    # -------------------------

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request ID for tracking and observability"
    )

    # -------------------------
    # Model Selection
    # -------------------------

    model: str = Field(
        ...,
        examples=[
            "gpt-4o",
            "llama-3.3-70b-versatile",
            "auto",
        ],
    )

    routing_policy: str | None = Field(
        default="complexity",
        examples=[
            "cost",
            "complexity",
            "balanced",
        ],
    )

    # -------------------------
    # Messages
    # -------------------------

    messages: list[Message]

    # -------------------------
    # Generation
    # -------------------------

    temperature: float | None = 1.0

    top_p: float | None = 1.0

    max_completion_tokens: int | None = None

    seed: int | None = None

    stop: str | list[str] | None = None

    # -------------------------
    # Streaming
    # -------------------------

    stream: bool = False

    # -------------------------
    # Tools
    # -------------------------

    tools: list[Tool] | None = None

    tool_choice: str | dict | None = "auto"

    # -------------------------
    # Output
    # -------------------------

    response_format: ResponseFormat | None = None

    # -------------------------
    # Provider Specific
    # -------------------------

    parameters: dict[str, Any] = Field(
        default_factory=dict
    )

    # =========================================================
    # HELPER METHODS FOR ROUTING
    # =========================================================

    def vision_in_request(self) -> bool:
        """
        Check if request needs vision capability.
        Returns True if any message has image_url content.
        """
        for msg in self.messages:
            # msg is a Message Pydantic model
            if isinstance(msg.content, list):
                for item in msg.content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        return True
        
        return False

    def tools_provided(self) -> bool:
        """
        Check if request has tools.
        """
        return bool(self.tools)

    def estimate_tokens(self) -> int:
        """
        Rough token estimation for request.
        
        Heuristic: 1 token ≈ 4 characters
        
        Returns:
            Estimated input tokens (minimum 10)
        """
        text = ""
        
        for msg in self.messages:
            # msg is a Message Pydantic model
            if isinstance(msg.content, str):
                text += msg.content + " "
            elif isinstance(msg.content, list):
                # Multimodal content
                for item in msg.content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text += item.get("text", "") + " "
        
        # Estimate: 1 token ≈ 4 chars
        token_estimate = len(text) // 4
        return max(10, token_estimate)

    def get_text_content(self) -> str:
        """
        Extract all text content from messages.
        Useful for complexity analysis and logging.
        
        Returns:
            Concatenated text from all messages
        """
        text = ""
        
        for msg in self.messages:
            if isinstance(msg.content, str):
                text += msg.content + " "
            elif isinstance(msg.content, list):
                for item in msg.content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text += item.get("text", "") + " "
        
        return text.strip()


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