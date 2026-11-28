"""Endpoints that describe the models this service can reach."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from dependencies.pagination import PaginationDep
from schemas.models import ModelInfo, ModelsResponse
from services.llm import describe_model, list_models

router = APIRouter(tags=["models"])


@router.get(
    "/models",
    summary="List available models",
    description="Everything configured in .env plus whatever Ollama has pulled "
                "locally, with prices read from the LiteLLM cost map.",
    response_model=ModelsResponse,
    status_code=status.HTTP_200_OK,
    response_description="One page of the models this service can call",
)
async def get_models(
    pagination: PaginationDep,
    provider: Annotated[
        str | None,
        Query(
            min_length=2,
            max_length=40,
            description="Keep only one provider, e.g. anthropic or ollama_chat",
        ),
    ] = None,
) -> ModelsResponse:
    models = await list_models(provider)
    skip, limit = pagination["skip"], pagination["limit"]
    return ModelsResponse(
        count=len(models),
        skip=skip,
        limit=limit,
        models=models[skip : skip + limit],
    )


@router.get(
    "/models/{name:path}",
    summary="Describe one model",
    description="Prices, context window and capabilities for a single model. "
                "The name contains a slash, which is why the path accepts one.",
    response_model=ModelInfo,
    responses={404: {"description": "Nothing known about this model"}},
)
async def get_model(
    name: Annotated[
        str,
        Path(
            min_length=1,
            description="Full LiteLLM name, e.g. anthropic/claude-haiku-5-5",
        ),
    ],
) -> ModelInfo:
    info = describe_model(name)
    known = {model["name"] for model in await list_models()}
    if name not in known and info["input_cost_per_1m"] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nothing known about '{name}'. Try GET /api/v1/models.",
        )
    return ModelInfo(**info)
