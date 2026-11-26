"""Τα σχήματα εισόδου και εξόδου του /ask."""
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
        description="Η ερώτηση προς το μοντέλο",
    )
    model: str | None = Field(
        default=None,
        description="Παράκαμψη του προεπιλεγμένου μοντέλου, π.χ. ollama_chat/llama3.2:1b",
    )


class AskResponse(BaseModel):
    answer: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    seconds: float
