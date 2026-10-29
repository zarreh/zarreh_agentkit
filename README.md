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
| `api.health` | `build_health_router` — rate-limited `GET /healthz` |
| `cost` | `CostTrackingHandler` + `CostEntry` — per-node token & cost attribution |
| `serialization` | `stream_graph_events` — LangGraph `astream_events` → SSE payloads, one per genuine node boundary (`name == metadata["langgraph_node"]`), so conditional-edge routers do not surface as steps |
| `guardrails.budget` | `Budget` + `budget_breach_reason` — the tool-call/wall-clock ceiling; breach *response* stays app-specific |
| `guardrails.grounding` | `grounding_confidence`, `count_unsupported`, `unsupported_claims_feedback` — aggregation of per-claim grounding judgments; the claim/judgment schemas stay app-specific |
| `guardrails.injection` | `INJECTION_PATTERNS` + `first_matching_rule` — the deterministic, named-rule injection screen under an LLM check |
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

**v0.2.1** filters `stream_graph_events` to genuine node boundaries and gives
`configure_logging` an `extra_processors` hook (for a redactor).

**v0.3** is a correctness release driven by consumers that had forked the
library to work around it: `build_tracing_callbacks` binds the tracer to a
`langsmith.Client` carrying the key (the ambient-env version 401'd whenever the
key only lived in `.env`), and `CostTrackingHandler` reads the node from the
start event, falls back to `usage_metadata` for structured-output calls, and
prices dated model snapshots by family. See `CHANGELOG.md`.

**v0.4** extracts the run infrastructure that had five or six copies across
consumers: the events/costs half of every `RunStore`, the run executor loop,
the replay-then-tail SSE stream, the prompt loader and the health route. Each
consumer keeps what a run is *about* — its `runs` table, initial state, node
set and what "finished" means.

**v0.5** promotes the grounding-judgment aggregation (two services) and the
deterministic injection screen (two services, catalogues merged).

Still deliberately absent, because the second occurrence did not share a core:

- `retrieval` — the two Qdrant consumers diverge (one uses `langchain-qdrant`
  stores over two corpora with a keyword fallback; the other a raw client with
  a mandatory per-record filter). Revisit when a third consumer settles it.
- log/text redaction — still one service. Another service's output scanner
  *blocks* leaks rather than redacting them, which is a different primitive.
- output scanning — the rules (PIN disclosure, cross-account references,
  clinical claim coverage) are domain policy, not mechanism.
- `mcp` — no consumer exports an MCP server yet.
