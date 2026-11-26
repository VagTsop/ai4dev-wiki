"""Endpoint για μία ερώτηση σε LLM."""
from fastapi import APIRouter, HTTPException, status

from schemas.ask import AskRequest, AskResponse
from services.llm import LLMError, ask_model

router = APIRouter(
    tags=["ask"],
    responses={502: {"description": "Σφάλμα παρόχου"}},
)


@router.post(
    "/ask",
    summary="Ερώτηση σε LLM",
    description="Στέλνει μία ερώτηση σε ένα μοντέλο και επιστρέφει την απάντηση "
                "μαζί με tokens, κόστος και χρόνο.",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    response_description="Η απάντηση του μοντέλου με τις μετρικές της",
)
async def ask(payload: AskRequest) -> AskResponse:
    try:
        result = await ask_model(payload.question, payload.model)
    except LLMError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return AskResponse(**result)
