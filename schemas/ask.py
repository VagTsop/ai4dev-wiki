"""Request and response schemas for the /ask endpoints."""
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
        description="The question to send to the model",
    )
    model: str | None = Field(
        default=None,
        description="Override the default model, e.g. ollama_chat/llama3.2:1b",
    )
    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="0 keeps answers predictable, higher values sample more freely",
    )
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        le=8000,
        description="Hard ceiling on the answer length. The reply is cut if it is reached",
    )


class AskResponse(BaseModel):
    answer: str
    model: str
    finish_reason: str | None = Field(
        default=None,
        description="'stop' when the model finished, 'length' when max_tokens cut it off",
    )
    tokens_in: int
    tokens_out: int
    cost_usd: float
    seconds: float
