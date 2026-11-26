# ai4dev-wiki

A Q&A assistant over the material of the **AI for Developers** programme
(Athens University of Economics and Business).

Built incrementally, one module of the curriculum at a time.

## What it does today

A FastAPI service that sends a question to any LLM — local or cloud — and returns
the answer together with **token usage, cost and latency**.

```http
POST /api/v1/ask
{ "question": "What is the capital of Crete?", "model": "ollama_chat/llama3.2:1b" }
```

```json
{
  "answer": "...",
  "model": "ollama_chat/llama3.2:1b",
  "tokens_in": 39,
  "tokens_out": 16,
  "cost_usd": 0.0,
  "seconds": 3.43
}
```

The `model` field is optional; when omitted, the `MODEL` entry from `.env` is used.
Switching between a cloud provider and a model running on your own machine is a
one-string change — everything else stays the same.

## Getting started

```bash
uv sync
cp .env.example .env     # then fill in your API key
uv run fastapi dev main.py
```

Interactive docs: <http://localhost:8000/docs>

## Layout

```
main.py           the FastAPI application
routers/          HTTP endpoints
schemas/          Pydantic models for requests and responses
services/         model calls and metrics, with no knowledge of HTTP
```

The separation matters: `services/` never imports FastAPI, so the same code can be
driven from a CLI, a scheduled job or a test.

## Roadmap

- [x] Service with a single endpoint, model switching, cost accounting
- [ ] Side-by-side comparison of several models, run concurrently
- [ ] Prompt engineering: system prompts, few-shot examples, structured output
- [ ] State management, timeouts, rate limits
- [ ] RAG over the course slides and repositories
- [ ] Agent with search and code-execution tools

## Built with

uv · FastAPI · Pydantic · LiteLLM · Ollama
