"""Endpoints for a conversation that remembers what was said."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from schemas.chat import ChatRequest, ChatResponse, ConversationResponse
from services import conversations
from services.llm import LLMError, call_model

router = APIRouter(
    tags=["chat"],
    responses={404: {"description": "Conversation not found"}},
)

ConversationId = Annotated[
    str,
    Path(min_length=1, max_length=64, description="Returned by POST /chat"),
]


def _require(conversation_id: str):
    conversation = conversations.get(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No conversation with id '{conversation_id}'.",
        )
    return conversation


@router.post(
    "/chat",
    summary="Send a message in a conversation",
    description="Starts a conversation when conversation_id is omitted, otherwise "
                "continues the existing one. The whole history is sent to the model "
                "on every turn, which is why tokens_in keeps growing.",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    response_description="The reply, plus the cost of this turn and of the conversation",
)
async def chat(payload: ChatRequest) -> ChatResponse:
    if payload.conversation_id:
        conversation = _require(payload.conversation_id)
    else:
        conversation = conversations.create(payload.system)

    conversation.messages.append({"role": "user", "content": payload.message})

    try:
        result = await call_model(
            conversation.messages,
            payload.model,
            payload.temperature,
            payload.max_tokens,
        )
    except LLMError:
        # This endpoint still catches, because it has cleaning up to do: drop the
        # question that never got an answer, so the history stays a clean
        # alternation of user and assistant turns. Translating the error into a
        # response is not our job, so it is re-raised for the handler.
        conversation.messages.pop()
        raise

    conversation.messages.append({"role": "assistant", "content": result["answer"]})
    conversation.cost_total_usd = round(
        conversation.cost_total_usd + result["cost_usd"], 8
    )

    return ChatResponse(
        conversation_id=conversation.id,
        turns=conversation.turns,
        cost_total_usd=conversation.cost_total_usd,
        **result,
    )


@router.get(
    "/chat/{conversation_id}",
    summary="Read a conversation",
    description="The full message list, system prompt included, exactly as it is "
                "sent to the model.",
    response_model=ConversationResponse,
)
async def read_conversation(conversation_id: ConversationId) -> ConversationResponse:
    conversation = _require(conversation_id)
    return ConversationResponse(
        conversation_id=conversation.id,
        turns=conversation.turns,
        cost_total_usd=conversation.cost_total_usd,
        messages=conversation.messages,
    )


@router.delete(
    "/chat/{conversation_id}",
    summary="Forget a conversation",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Deleted",
)
async def delete_conversation(conversation_id: ConversationId) -> None:
    _require(conversation_id)
    conversations.delete(conversation_id)
