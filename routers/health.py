"""Endpoint that reports whether this installation is actually usable."""
from typing import Annotated

from fastapi import APIRouter, Query, status

from schemas.health import HealthResponse
from services.health import report

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Check the environment",
    description="Which provider keys are configured, whether Ollama is reachable, "
                "and how many models can be priced. With probe=true every known "
                "model is called once with a one-token prompt, concurrently, so a "
                "broken provider is visible rather than guessed at.",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    response_description="Configuration and, optionally, live probe results",
)
async def health(
    probe: Annotated[
        bool,
        Query(description="Call every model once. Costs a fraction of a cent and takes as long as the slowest model"),
    ] = False,
) -> HealthResponse:
    return HealthResponse(**await report(probe))
