"""Response schemas for the /models endpoints."""
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str
    provider: str
    local: bool = Field(description="True when the model runs on this machine")
    input_cost_per_1m: float | None = Field(
        default=None,
        description="US dollars per million input tokens. None when unknown",
    )
    output_cost_per_1m: float | None = None
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    supports_vision: bool | None = None
    supports_function_calling: bool | None = None


class ModelsResponse(BaseModel):
    count: int
    models: list[ModelInfo]
