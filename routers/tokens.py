"""Endpoint that measures text in tokens before anything is sent."""
from fastapi import APIRouter, HTTPException, status

from schemas.tokens import TokensRequest, TokensResponse
from services.llm import LLMError, count_tokens

router = APIRouter(tags=["tokens"])


@router.post(
    "/tokens",
    summary="Count tokens for a piece of text",
    description="Measures text with the tokenizer of the given model and prices it "
                "as input. The same text costs a different number of tokens on "
                "different model families.",
    response_model=TokensResponse,
    status_code=status.HTTP_200_OK,
    response_description="Token count, character count and the resulting input cost",
)
async def tokens(payload: TokensRequest) -> TokensResponse:
    try:
        result = count_tokens(payload.text, payload.model)
    except LLMError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return TokensResponse(**result)
