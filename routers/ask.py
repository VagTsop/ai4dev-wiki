"""Endpoint for a single question to an LLM."""
from fastapi import APIRouter, HTTPException, status

from schemas.ask import AskRequest, AskResponse
from services.llm import LLMError, ask_model

router = APIRouter(
    tags=["ask"],
    responses={502: {"description": "Provider error"}},
)


@router.post(
    "/ask",
    summary="Ask an LLM",
    description="Sends a single question to a model and returns the answer "
                "along with token usage, cost and latency.",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    response_description="The model's answer with its metrics",
)
async def ask(payload: AskRequest) -> AskResponse:
    try:
        result = await ask_model(payload.question, payload.model)
    except LLMError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return AskResponse(**result)
