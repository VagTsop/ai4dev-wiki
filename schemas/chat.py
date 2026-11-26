"""Request and response schemas for the /chat endpoints."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="What the user says in this turn",
    )
    conversation_id: str | None = Field(
        default=None,
        description="Continue an existing conversation. Omit to start a new one",
    )
    system: str | None = Field(
        default=None,
        max_length=2000,
        description="Behaviour for the whole conversation. Only read when a new one starts",
    )
    model: str | None = Field(default=None, description="Override the default model")
    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="0 keeps answers predictable, higher values sample more freely",
    )
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        le=8000,
        description="Hard ceiling on the answer length. The reply is cut if it is reached",
    )


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    model: str
    turns: int = Field(description="How many user messages this conversation holds")
    finish_reason: str | None = Field(
        default=None,
        description="'stop' when the model finished, 'length' when max_tokens cut it off",
    )
    tokens_in: int
    tokens_out: int
    cost_usd: float = Field(description="Cost of this turn alone")
    cost_total_usd: float = Field(description="Cost of the whole conversation so far")
    seconds: float


class Message(BaseModel):
    role: str
    content: str


class ConversationResponse(BaseModel):
    conversation_id: str
    turns: int
    cost_total_usd: float
    messages: list[Message]
