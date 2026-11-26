"""Model calls, with timing and cost metrics. Knows nothing about HTTP."""
import os
import time

from dotenv import load_dotenv

load_dotenv()

import litellm

DEFAULT_MODEL = os.getenv("MODEL", "anthropic/claude-haiku-5-5")


class LLMError(Exception):
    """A failed model call, carrying the HTTP status the router should return."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def ask_model(question: str, model: str | None = None) -> dict:
    """Send a single question and return the answer along with its metrics."""
    model = model or DEFAULT_MODEL
    messages = [{"role": "user", "content": question}]

    start = time.perf_counter()
    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            num_retries=2,
        )
    except litellm.AuthenticationError:
        raise LLMError(f"Missing or invalid API key for '{model}'.", 401)
    except litellm.RateLimitError:
        raise LLMError("Rate limit exceeded. Please try again shortly.", 429)
    except litellm.APIConnectionError:
        raise LLMError(f"Could not reach the provider for '{model}'.", 503)
    except litellm.APIError as exc:
        raise LLMError(f"Provider error: {exc}", 502)
    seconds = time.perf_counter() - start

    usage = response.usage
    try:
        cost = litellm.completion_cost(completion_response=response)
    except Exception:
        # The model is missing from the LiteLLM cost map, so we cannot price it.
        cost = 0.0

    return {
        "answer": response.choices[0].message.content,
        "model": model,
        "tokens_in": usage.prompt_tokens,
        "tokens_out": usage.completion_tokens,
        "cost_usd": round(cost, 8),
        "seconds": round(seconds, 2),
    }
