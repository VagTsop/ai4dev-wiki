"""Request and response schemas for the /ask endpoint."""
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


class AskResponse(BaseModel):
    answer: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    seconds: float
