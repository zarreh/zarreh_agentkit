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
| `observability` | `configure_logging` (with an `extra_processors` hook that runs just before the renderer, e.g. a redactor) / `get_logger` + a shared `correlation_id` `ContextVar` + `build_tracing_callbacks` (LangSmith tracer, gated on whether an API key is configured) |
| `api.middleware` | `MaxBodySizeMiddleware` — honest 413 at the ASGI layer (OWASP API4) |
| `api.rate_limit` | `build_limiter` / `default_rate_limit` — per-route slowapi limiting |
| `cost` | `CostTrackingHandler` + `CostEntry` — per-node token & cost attribution |
| `serialization` | `stream_graph_events` — LangGraph `astream_events` → SSE payloads, one per genuine node boundary (`name == metadata["langgraph_node"]`), so conditional-edge routers do not surface as steps |
| `guardrails.budget` | `Budget` + `budget_breach_reason` — the tool-call/wall-clock ceiling; breach *response* stays app-specific |
| `guardrails.projection` | `project_fields` — least-privilege allowlist projection of a Pydantic model; the allowlist itself stays app-specific |
| `evals` | `run_eval_cli` — the run/print/gate shell behind `make eval`; scenario definitions and metrics stay app-specific |
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
library.

**v0.2** adds `observability.build_tracing_callbacks` (identical in three
consuming services), `guardrails.budget` and `guardrails.projection` (two
occurrences each), and the `evals` runner shell (one real implementation, one
consumer waiting on it — promoted because the shell itself is what the
second service needs, not a new metric set).

Still deliberately absent, pending a validated second occurrence:
`retrieval` (no consumer has yet needed the intended vector-store shape),
`mcp` (two services are meant to jointly harden the export convention before
it lands here — neither has yet), and any general-purpose log/text redaction
primitive (only one service has this shape so far).
