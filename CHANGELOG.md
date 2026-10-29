# Changelog

## 0.5.0

### Added
- `guardrails.grounding` — `grounding_confidence`, `count_unsupported`,
  `unsupported_claims_feedback`, `ClaimJudgmentLike`.
- `guardrails.injection` — `INJECTION_PATTERNS` (union of two services'
  catalogues, named rules) and `first_matching_rule`.

### Deferred (documented in the README)
- `retrieval`, redaction, output scanning, `mcp`.

## 0.4.0

### Added
- `runs.RunEventLog` — SQLite `<prefix>_events` / `<prefix>_costs` tables with
  `append_event`, `get_events`, `record_costs`, `get_costs`. Consumers subclass
  it and keep their own `runs` table, so existing databases are unchanged.
- `runs.execute_run` — streams a graph, persists every genuine node step,
  records per-node cost (a `CostTrackingHandler` is always attached), calls an
  app `finalize(final_state)`, and marks the run failed on any exception.
- `runs.replay_and_tail` — replay-then-tail SSE over persisted events. Drains
  once more after the run is seen as finished, closing a window where an event
  written between the last read and the status check was never streamed.
- `serialization.iter_node_outputs` and `serialization.json_default`.
- `prompts.PromptLoader`, `api.health.build_health_router`.
- API docs pages for `runs`, `prompts`, `guardrails`, `evals`.

### Changed
- `serialization.stream_graph_events` is implemented on `iter_node_outputs`
  (behaviour unchanged).

## 0.3.0

### Fixed
- `observability.build_tracing_callbacks` binds `LangChainTracer` to a cached
  `langsmith.Client(api_key=...)`. Previously the key only gated attachment and
  the tracer read an ambient `LANGSMITH_API_KEY`, which pydantic-settings never
  exports from `.env` — every upload failed with a 401.
- `cost.CostTrackingHandler` attributes calls to the right node: LangChain
  delivers `langgraph_node` metadata on `on_chat_model_start`/`on_llm_start`,
  not `on_llm_end`, so every entry was previously `"unknown"`.
- `cost.CostTrackingHandler` falls back to the message's `usage_metadata` when
  `llm_output` carries no token usage (structured-output calls), instead of
  recording zero tokens.
- `cost.estimate_cost_usd` prices dated snapshots (`gpt-4o-mini-2024-07-18`)
  as their longest listed family name instead of $0.

### Changed
- `langsmith` is now a declared dependency (previously transitive).

## 0.2.1
- `serialization.stream_graph_events` emits only genuine node boundaries
  (`name == metadata["langgraph_node"]`).
- `observability.configure_logging(environment, extra_processors=())`.

## 0.2.0
- `observability.build_tracing_callbacks`, `guardrails.budget`,
  `guardrails.projection`, `evals.run_eval_cli`.

## 0.1.0
- `settings`, `observability`, `api.middleware`, `api.rate_limit`, `cost`,
  `serialization`, `architecture` contracts.
