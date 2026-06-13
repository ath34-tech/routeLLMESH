from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ModelCreate(BaseModel):

    provider_id: int

    model_name: str = Field(
        ...,
        max_length=100,
        examples=["gpt-4o"],
    )

    display_name: str = Field(
        ...,
        examples=["GPT-4o"],
    )

    context_window: int = 128000

    input_cost: float = 0.0

    output_cost: float = 0.0

    priority: int = 1

    fallback_order: int = 1

    supports_stream: bool = True

    supports_tools: bool = False

    supports_vision: bool = False

    supports_reasoning: bool = False

    enabled: bool = True


class ModelUpdate(BaseModel):

    display_name: str | None = None

    context_window: int | None = None

    input_cost: float | None = None

    output_cost: float | None = None

    priority: int | None = None

    fallback_order: int | None = None

    supports_stream: bool | None = None

    supports_tools: bool | None = None

    supports_vision: bool | None = None

    supports_reasoning: bool | None = None

    enabled: bool | None = None


class ModelResponse(BaseModel):

    id: int

    provider_id: int

    model_name: str

    display_name: str

    context_window: int

    input_cost: float

    output_cost: float

    priority: int

    fallback_order: int

    supports_stream: bool

    supports_tools: bool

    supports_vision: bool

    supports_reasoning: bool

    enabled: bool

    model_config = ConfigDict(
        from_attributes=True,
    )