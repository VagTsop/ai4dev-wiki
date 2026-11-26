"""Endpoint that asks several models the same question at once."""
from fastapi import APIRouter, status

from schemas.compare import CompareRequest, CompareResponse
from services.llm import compare_models

router = APIRouter(tags=["compare"])


@router.post(
    "/compare",
    summary="Compare models side by side",
    description="Sends the same question to several models concurrently and returns "
                "every answer with its own tokens, cost and latency. A model that "
                "fails is reported in its own entry without affecting the others.",
    response_model=CompareResponse,
    status_code=status.HTTP_200_OK,
    response_description="One entry per model, plus totals for the whole run",
)
async def compare(payload: CompareRequest) -> CompareResponse:
    result = await compare_models(payload.question, payload.models)
    return CompareResponse(**result)
