# ai4dev-wiki

A Q&A assistant over the material of the **AI for Developers** programme
(Athens University of Economics and Business).

Built incrementally, one module of the curriculum at a time.

## What it does today

A FastAPI service that talks to any LLM — local or cloud — through one interface,
and reports what every call cost.

| Endpoint | What it does |
|---|---|
| `POST /api/v1/ask` | One question, one answer, with tokens, cost and latency |
| `POST /api/v1/ask/stream` | The same, streamed token by token over server-sent events |
| `POST /api/v1/chat` | A conversation that remembers, with an optional system prompt |
| `GET /api/v1/chat/{id}` | The full message list as it is sent to the model |
| `DELETE /api/v1/chat/{id}` | Forget a conversation |
| `POST /api/v1/compare` | The same question to several models, run concurrently |
| `GET /api/v1/models` | Available models with prices and capabilities |
| `GET /api/v1/models/{name}` | Details for one model |
| `POST /api/v1/tokens` | Measure text in tokens and price it before sending |

Switching between a cloud provider and a model running on your own machine is a
one-string change — everything else stays the same.

```http
POST /api/v1/ask
{ "question": "What is the capital of Crete?", "model": "ollama_chat/llama3.2:1b" }
```

```json
{
  "answer": "...",
  "model": "ollama_chat/llama3.2:1b",
  "finish_reason": "stop",
  "tokens_in": 39,
  "tokens_out": 16,
  "cost_usd": 0.0,
  "seconds": 3.43
}
```

## Getting started

```bash
uv sync
cp .env.example .env     # then fill in your API key
uv run fastapi dev main.py
```

Interactive docs: <http://localhost:8000/docs>

Streaming cannot be rendered by Swagger, so try that one with curl:

```bash
curl -N -X POST http://localhost:8000/api/v1/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"Name three Greek islands."}'
```

## Layout

```
main.py           the FastAPI application
routers/          HTTP endpoints
schemas/          Pydantic models for requests and responses
services/         model calls and state, with no knowledge of HTTP
```

The separation matters: `services/` never imports FastAPI, so the same code can be
driven from a CLI, a scheduled job or a test.

## Notes from building it

A few things that are easy to miss and cost real time:

- `litellm.completion()` blocks. Inside an `async def` route it freezes the whole
  server for the length of the call, so everything here uses `acompletion`.
- `/compare` starts every model before awaiting any of them, so a run takes as
  long as the slowest model rather than the sum of all of them.
- Conversations live in a dictionary in memory. Restarting loses them, and more
  than one worker process would split them.
- Not every model accepts every parameter. `claude-haiku-5-5` rejects any
  `temperature` other than 1, which the cost map flags as `supports_sampling_params`.
- Greek text costs roughly four times the tokens of the equivalent English: the
  same question measured 8 tokens in English and 32 in Greek.

## Roadmap

- [x] Service with a single endpoint, model switching, cost accounting
- [x] Side-by-side comparison of several models, run concurrently
- [x] Conversations with history and a system prompt
- [x] Streaming responses
- [x] Model catalogue and token measurement
- [ ] Prompt engineering: few-shot examples, structured output
- [ ] Reliability: timeouts, rate limits, spending caps
- [ ] RAG over the course slides and repositories
- [ ] Agent with search and code-execution tools

## Built with

uv · FastAPI · Pydantic · LiteLLM · Ollama
