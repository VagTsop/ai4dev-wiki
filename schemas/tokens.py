"""Request and response schemas for the /tokens endpoint."""
from pydantic import BaseModel, Field


class TokensRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=100_000,
        description="The text to measure",
    )
    model: str | None = Field(
        default=None,
        description="Tokenizers differ per model family, so the count depends on this",
    )


class TokensResponse(BaseModel):
    model: str
    tokens: int
    characters: int
    chars_per_token: float = Field(
        description="Lower means the text is expensive to encode. Greek sits well below English",
    )
    cost_as_input_usd: float = Field(
        description="What this text would cost if sent as input to that model",
    )
