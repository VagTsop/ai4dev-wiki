"""Response schemas for the /health endpoint."""
from pydantic import BaseModel, Field


class ProviderStatus(BaseModel):
    name: str
    env_var: str
    key_configured: bool


class OllamaStatus(BaseModel):
    base_url: str
    reachable: bool
    models: list[str] = Field(default_factory=list)


class ProbeResult(BaseModel):
    model: str
    ok: bool
    seconds: float | None = None
    detail: str | None = Field(
        default=None,
        description="Why the call failed. A 401 here means the route works and only the key is missing",
    )


class HealthResponse(BaseModel):
    status: str = Field(description="'ok' when the default model can be called, otherwise 'degraded'")
    default_model: str
    providers: list[ProviderStatus]
    ollama: OllamaStatus
    models_known: int
    cost_map_entries: int = Field(description="How many models LiteLLM can price")
    probes: list[ProbeResult] | None = Field(
        default=None,
        description="Only present when the request asked for probe=true",
    )
