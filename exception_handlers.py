"""Turn exceptions raised deep in the service layer into HTTP responses.

Without this, every endpoint has to catch LLMError and translate it by hand. The
service raises, FastAPI answers, and the routers stay about their own job.
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from services.llm import LLMError

logger = logging.getLogger(__name__)


def register(app: FastAPI) -> None:
    @app.exception_handler(LLMError)
    async def handle_llm_error(request: Request, exc: LLMError) -> JSONResponse:
        """A model call failed for a reason we understand and can explain."""
        logger.warning(
            "%s %s -> %s: %s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.message,
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        """Anything we did not foresee. Logged in full, reported without detail.

        The traceback belongs in the log, not in the response: it would tell a
        stranger about the inside of the application.
        """
        logger.error(
            "Unhandled error on %s %s",
            request.method,
            request.url.path,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
