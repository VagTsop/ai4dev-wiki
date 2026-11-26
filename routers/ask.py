"""Endpoints for a single question to an LLM."""
import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from schemas.ask import AskRequest, AskResponse
from services.llm import LLMError, ask_model, stream_model

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
        result = await ask_model(
            payload.question,
            payload.model,
            payload.temperature,
            payload.max_tokens,
        )
    except LLMError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return AskResponse(**result)


@router.post(
    "/ask/stream",
    summary="Ask an LLM and receive the answer as it is written",
    description="Server-sent events. Every event carries either a piece of the "
                "answer or, as the last one, the metrics for the whole call. "
                "Swagger cannot render a stream, so try this with curl.",
    response_description="A text/event-stream of JSON events",
)
async def ask_stream(payload: AskRequest) -> StreamingResponse:
    async def events():
        # Once the response has started there is no way back to an HTTP status
        # code, so a failure has to travel inside the stream itself.
        try:
            async for event in stream_model(
                payload.question,
                payload.model,
                payload.temperature,
                payload.max_tokens,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except LLMError as exc:
            yield f"data: {json.dumps({'error': exc.message}, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
