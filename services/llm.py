"""Η επικοινωνία με το μοντέλο, μαζί με μετρικές χρόνου και κόστους."""
import os
import time

from dotenv import load_dotenv

load_dotenv()

import litellm

DEFAULT_MODEL = os.getenv("MODEL", "anthropic/claude-haiku-5-5")


class LLMError(Exception):
    """Σφάλμα κατά την κλήση του μοντέλου, με κωδικό HTTP για τον router."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def ask_model(question: str, model: str | None = None) -> dict:
    """Στέλνει μία ερώτηση και επιστρέφει την απάντηση με τις μετρικές της."""
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
        raise LLMError(f"Μη έγκυρο ή απόν κλειδί API για το «{model}».", 401)
    except litellm.RateLimitError:
        raise LLMError("Υπέρβαση ορίου αιτημάτων. Δοκιμάστε ξανά σε λίγο.", 429)
    except litellm.APIConnectionError:
        raise LLMError(f"Αδύνατη η σύνδεση με τον πάροχο του «{model}».", 503)
    except litellm.APIError as exc:
        raise LLMError(f"Σφάλμα από τον πάροχο: {exc}", 502)
    seconds = time.perf_counter() - start

    usage = response.usage
    try:
        cost = litellm.completion_cost(completion_response=response)
    except Exception:
        cost = 0.0

    return {
        "answer": response.choices[0].message.content,
        "model": model,
        "tokens_in": usage.prompt_tokens,
        "tokens_out": usage.completion_tokens,
        "cost_usd": round(cost, 8),
        "seconds": round(seconds, 2),
    }
