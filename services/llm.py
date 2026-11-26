"""Model calls, with timing and cost metrics. Knows nothing about HTTP."""
import asyncio
import os
import time
from collections.abc import AsyncIterator

import httpx
from dotenv import load_dotenv

load_dotenv()

import litellm

DEFAULT_MODEL = os.getenv("MODEL", "anthropic/claude-haiku-5-5")
COMPARE_MODELS = [
    name.strip()
    for name in os.getenv("COMPARE_MODELS", DEFAULT_MODEL).split(",")
    if name.strip()
]
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

PER_MILLION = 1_000_000


class LLMError(Exception):
    """A failed model call, carrying the HTTP status the router should return."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _translate(exc: Exception, model: str) -> LLMError:
    """Map a LiteLLM exception onto a meaningful HTTP status."""
    if isinstance(exc, litellm.AuthenticationError):
        return LLMError(f"Missing or invalid API key for '{model}'.", 401)
    if isinstance(exc, litellm.RateLimitError):
        return LLMError("Rate limit exceeded. Please try again shortly.", 429)
    if isinstance(exc, litellm.APIConnectionError):
        return LLMError(f"Could not reach the provider for '{model}'.", 503)
    if isinstance(exc, litellm.BadRequestError):
        return LLMError(f"The provider rejected the request: {exc}", 400)
    return LLMError(f"Provider error: {exc}", 502)


def _price(response) -> float:
    try:
        return litellm.completion_cost(completion_response=response)
    except Exception:
        # The model is missing from the LiteLLM cost map, so we cannot price it.
        return 0.0


def _options(temperature: float | None, max_tokens: int | None) -> dict:
    """Only send optional parameters that were actually asked for."""
    extra = {}
    if temperature is not None:
        extra["temperature"] = temperature
    if max_tokens is not None:
        extra["max_tokens"] = max_tokens
    return extra


async def call_model(
    messages: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    """Send a full message list and return the reply with its metrics."""
    model = model or DEFAULT_MODEL

    start = time.perf_counter()
    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            num_retries=2,
            **_options(temperature, max_tokens),
        )
    except Exception as exc:
        raise _translate(exc, model) from exc
    seconds = time.perf_counter() - start

    usage = response.usage
    return {
        "answer": response.choices[0].message.content,
        "model": model,
        "finish_reason": response.choices[0].finish_reason,
        "tokens_in": usage.prompt_tokens,
        "tokens_out": usage.completion_tokens,
        "cost_usd": round(_price(response), 8),
        "seconds": round(seconds, 2),
    }


async def ask_model(
    question: str,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    """Send a single question with no conversation history."""
    messages = [{"role": "user", "content": question}]
    return await call_model(messages, model, temperature, max_tokens)


async def stream_model(
    question: str,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> AsyncIterator[dict]:
    """Yield the answer piece by piece, then a final event with the metrics.

    Each yielded dict is either a delta while the model writes, or a single
    closing event carrying tokens, cost and latency.
    """
    model = model or DEFAULT_MODEL
    messages = [{"role": "user", "content": question}]

    start = time.perf_counter()
    try:
        stream = await litellm.acompletion(
            model=model,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
            **_options(temperature, max_tokens),
        )
    except Exception as exc:
        raise _translate(exc, model) from exc

    tokens_in = tokens_out = 0
    async for chunk in stream:
        usage = getattr(chunk, "usage", None)
        if usage:
            tokens_in = usage.prompt_tokens or tokens_in
            tokens_out = usage.completion_tokens or tokens_out
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield {"delta": delta}

    cost = 0.0
    info = describe_model(model)
    if info["input_cost_per_1m"] is not None:
        cost = (
            tokens_in * info["input_cost_per_1m"]
            + tokens_out * info["output_cost_per_1m"]
        ) / PER_MILLION

    yield {
        "done": True,
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost, 8),
        "seconds": round(time.perf_counter() - start, 2),
    }


async def compare_models(question: str, models: list[str] | None = None) -> dict:
    """Ask several models the same question at the same time.

    Every model is started before any of them is awaited, so the comparison takes
    as long as the slowest model rather than the sum of all of them. A model that
    fails does not cancel the rest: its entry carries an error instead of an
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


def describe_model(name: str) -> dict:
    """Read a model's prices and capabilities from the LiteLLM cost map."""
    entry = {
        "name": name,
        "provider": name.split("/")[0] if "/" in name else "unknown",
        "local": name.startswith("ollama"),
        "input_cost_per_1m": None,
        "output_cost_per_1m": None,
        "max_input_tokens": None,
        "max_output_tokens": None,
        "supports_vision": None,
        "supports_function_calling": None,
    }
    try:
        info = litellm.get_model_info(model=name)
    except Exception:
        # Not in the cost map: a brand new model, or a local one.
        return entry

    def per_million(key: str) -> float | None:
        value = info.get(key)
        return round(value * PER_MILLION, 4) if value is not None else None

    entry.update(
        {
            "input_cost_per_1m": per_million("input_cost_per_token"),
            "output_cost_per_1m": per_million("output_cost_per_token"),
            "max_input_tokens": info.get("max_input_tokens"),
            "max_output_tokens": info.get("max_output_tokens"),
            "supports_vision": info.get("supports_vision"),
            "supports_function_calling": info.get("supports_function_calling"),
        }
    )
    return entry


def count_tokens(text: str, model: str | None = None) -> dict:
    """Count how many tokens a piece of text costs for a given model.

    Tokenizers differ between model families, so the same text does not cost the
    same number of tokens everywhere.
    """
    model = model or DEFAULT_MODEL
    try:
        tokens = litellm.token_counter(model=model, text=text)
    except Exception as exc:
        raise LLMError(f"Cannot tokenize for '{model}': {exc}", 400) from exc

    info = describe_model(model)
    price = info["input_cost_per_1m"]
    characters = len(text)
    return {
        "model": model,
        "tokens": tokens,
        "characters": characters,
        "chars_per_token": round(characters / tokens, 2) if tokens else 0.0,
        "cost_as_input_usd": round(tokens * price / PER_MILLION, 8) if price else 0.0,
    }


async def local_model_names() -> list[str]:
    """Ask the running Ollama server which models it has pulled."""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
    except Exception:
        return []
    return [f"ollama_chat/{item['name']}" for item in response.json().get("models", [])]


async def list_models(provider: str | None = None) -> list[dict]:
    """Every model this service knows about: configured in .env plus local ones."""
    names: set[str] = set(COMPARE_MODELS)
    for key in ("MODEL", "MODEL_LOCAL", "MODEL_OPENROUTER_FREE"):
        value = os.getenv(key)
        if value:
            names.add(value.strip())
    names.update(await local_model_names())

    models = [describe_model(name) for name in sorted(names)]
    if provider:
        models = [m for m in models if m["provider"] == provider]
    return models
