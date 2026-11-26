"""Request and response schemas for the /compare endpoint."""
from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
        description="The question to send to every model",
    )
    models: list[str] | None = Field(
        default=None,
        min_length=1,
        max_length=6,
        description="Models to compare. Defaults to COMPARE_MODELS from .env",
    )


class CompareResult(BaseModel):
    model: str
    answer: str | None = None
    error: str | None = Field(
        default=None,
        description="Set when this model failed; the others still return",
    )
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    seconds: float = 0.0


class CompareResponse(BaseModel):
    question: str
    seconds_total: float = Field(
        description="Wall-clock time for the whole comparison, not the sum of the parts",
    )
    cost_total_usd: float
    results: list[CompareResult]
