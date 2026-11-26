"""Model calls, with timing and cost metrics. Knows nothing about HTTP."""
import asyncio
import os
import time

from dotenv import load_dotenv

load_dotenv()

import litellm

DEFAULT_MODEL = os.getenv("MODEL", "anthropic/claude-haiku-5-5")
COMPARE_MODELS = [
    name.strip()
    for name in os.getenv("COMPARE_MODELS", DEFAULT_MODEL).split(",")
    if name.strip()
]


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


async def compare_models(question: str, models: list[str] | None = None) -> dict:
    """Ask several models the same question at the same time.

    Every model is started before any of them is awaited, so the comparison takes
    as long as the slowest model rather than the sum of all of them. A model that
    fails does not cancel the rest: its entry carries an ``error`` instead of an
    answer.
    """
    models = models or COMPARE_MODELS

    start = time.perf_counter()
    outcomes = await asyncio.gather(
        *(ask_model(question, name) for name in models),
        return_exceptions=True,
    )
    seconds_total = time.perf_counter() - start

    results = []
    for name, outcome in zip(models, outcomes):
        if isinstance(outcome, LLMError):
            results.append({"model": name, "error": outcome.message})
        elif isinstance(outcome, BaseException):
            results.append({"model": name, "error": f"Unexpected error: {outcome}"})
        else:
            results.append(outcome)

    return {
        "question": question,
        "seconds_total": round(seconds_total, 2),
        "cost_total_usd": round(sum(r.get("cost_usd", 0.0) for r in results), 8),
        "results": results,
    }
