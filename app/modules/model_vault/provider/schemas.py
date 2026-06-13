
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ProviderCreate(BaseModel):

    name: str = Field(
        ...,
        max_length=100,
        examples=["openai"],
    )

    api_key: str = Field(
        ...,
        examples=["sk-xxxxxxxx"],
    )

    base_url: str = Field(
        ...,
        examples=["https://api.openai.com/v1"],
    )

    adapter: str = Field(
        ...,
        examples=["openai"],
    )

    enabled: bool = True


class ProviderUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        max_length=100,
    )

    api_key: str | None = None

    base_url: str | None = None

    adapter: str | None = None

    enabled: bool | None = None


class ProviderResponse(BaseModel):

    id: int

    name: str

    base_url: str

    adapter: str

    enabled: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
