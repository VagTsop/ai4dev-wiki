"""Environment checks: what is configured, what is reachable, what actually answers.

This is the service equivalent of the setup scripts in the course repository. It
answers the question you ask yourself every time something breaks: is my key
there, is Ollama up, and does the model actually reply?
"""
import asyncio
import os

import litellm

from services.llm import (
    DEFAULT_MODEL,
    OLLAMA_BASE_URL,
    LLMError,
    ask_model,
    list_models,
    local_model_names,
)

PROVIDER_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

PROBE_TIMEOUT_SECONDS = 30


def providers() -> list[dict]:
    """Which provider keys are present in the environment."""
    return [
        {
            "name": name,
            "env_var": env_var,
            "key_configured": bool(os.getenv(env_var, "").strip()),
        }
        for name, env_var in PROVIDER_KEYS.items()
    ]


async def ollama_status() -> dict:
    names = await local_model_names()
    return {
        "base_url": OLLAMA_BASE_URL,
        "reachable": bool(names),
        "models": [name.split("/", 1)[1] for name in names],
    }


async def probe(model: str) -> dict:
    """Make the smallest possible real call, to see whether the route works.

    A failure is still informative. An authentication error means LiteLLM routed
    the request correctly and only the key is missing, which is exactly what you
    want to know about a provider you have not signed up for yet.
    """
    try:
        result = await asyncio.wait_for(
            ask_model("ping", model, max_tokens=1),
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return {
            "model": model,
            "ok": False,
            "detail": f"No reply within {PROBE_TIMEOUT_SECONDS}s.",
        }
    except LLMError as exc:
        return {"model": model, "ok": False, "detail": f"{exc.status_code}: {exc.message}"}
    except Exception as exc:
        return {"model": model, "ok": False, "detail": f"Unexpected error: {exc}"}
    return {"model": model, "ok": True, "seconds": result["seconds"]}


async def report(run_probes: bool = False) -> dict:
    """Everything worth knowing about this installation."""
    models = await list_models()
    ollama = await ollama_status()

    probes = None
    status = "ok"
    if run_probes:
        probes = list(
            await asyncio.gather(*(probe(model["name"]) for model in models))
        )
        default = next((p for p in probes if p["model"] == DEFAULT_MODEL), None)
        if default is not None and not default["ok"]:
            status = "degraded"
    else:
        provider = DEFAULT_MODEL.split("/")[0]
        env_var = PROVIDER_KEYS.get(provider)
        if env_var and not os.getenv(env_var, "").strip():
            status = "degraded"

    return {
        "status": status,
        "default_model": DEFAULT_MODEL,
        "providers": providers(),
        "ollama": ollama,
        "models_known": len(models),
        "cost_map_entries": len(litellm.model_cost),
        "probes": probes,
    }
