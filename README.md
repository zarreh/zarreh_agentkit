# zarreh-agentkit

Shared substrate for independent agent services: typed settings, observability
with correlation IDs, ASGI request middleware, per-node LLM cost accounting,
and a trace→SSE serialization bridge.

**Extracted from two working implementations, never designed up front.** Every
abstraction here had two real consumers before it was allowed to become one —
which is why the public surface is deliberately narrow.

## What it provides

| Module | What it carries |
|---|---|
| `settings` | `AgentSettings` — a `pydantic-settings` base; subclass per service, set `env_prefix` |
| `observability` | `configure_logging` / `get_logger` + a shared `correlation_id` `ContextVar` |
| `api.middleware` | `MaxBodySizeMiddleware` — honest 413 at the ASGI layer (OWASP API4) |
| `api.rate_limit` | `build_limiter` / `default_rate_limit` — per-route slowapi limiting |
| `cost` | `CostTrackingHandler` + `CostEntry` — per-node token & cost attribution |
| `serialization` | `stream_graph_events` — LangGraph `astream_events` → SSE payloads |
| `architecture` | Bundled import-linter contracts, checked in every consumer's CI |

## Install

```bash
# path dependency during development
uv add --editable ../zarreh_agentkit
# or as a git dependency once pushed
uv add "zarreh-agentkit @ git+https://github.com/zarreh/zarreh-agentkit"
```

## Development

```bash
uv sync --extra dev
make check   # ruff, mypy --strict, lint-imports, pytest (coverage gate 90)
```

## The extraction rule

A pattern needed **two independent occurrences** before it was promoted to this
library. `guardrails`, `retrieval`, `evals`, and `mcp` are deliberately absent
from v0.1 — no second implementation exists yet. They will be extracted at v0.2
once a second service proves the need.
