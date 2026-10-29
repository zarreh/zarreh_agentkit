# Changelog

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
