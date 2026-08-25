from langchain_core.outputs import LLMResult

from zarreh_agentkit.cost import (
    PRICE_PER_MILLION_TOKENS,
    CostTrackingHandler,
    estimate_cost_usd,
)


def test_estimate_known_model() -> None:
    # gpt-4o-mini: $0.15 / $0.60 per 1M
    assert estimate_cost_usd("gpt-4o-mini", 1_000_000, 0) == 0.15
    assert estimate_cost_usd("gpt-4o-mini", 0, 1_000_000) == 0.60


def test_estimate_unknown_model_is_zero() -> None:
    assert estimate_cost_usd("not-a-model", 5_000_000, 5_000_000) == 0.0


def test_price_table_non_empty() -> None:
    assert "gpt-4o-mini" in PRICE_PER_MILLION_TOKENS


def test_handler_attributes_cost_to_node() -> None:
    import uuid

    handler = CostTrackingHandler()
    result = LLMResult(
        generations=[[]],
        llm_output={
            "model_name": "gpt-4o-mini",
            "token_usage": {"prompt_tokens": 100, "completion_tokens": 50},
        },
    )
    handler.on_llm_end(result, run_id=uuid.uuid4(), metadata={"langgraph_node": "planner"})
    assert len(handler.entries) == 1
    entry = handler.entries[0]
    assert entry.node == "planner"
    assert entry.model == "gpt-4o-mini"
    assert entry.prompt_tokens == 100
    assert entry.completion_tokens == 50
    assert entry.cost_usd == estimate_cost_usd("gpt-4o-mini", 100, 50)


def test_handler_missing_metadata_defaults_to_unknown() -> None:
    import uuid

    handler = CostTrackingHandler()
    result = LLMResult(generations=[[]], llm_output=None)
    handler.on_llm_end(result, run_id=uuid.uuid4())
    assert handler.entries[0].node == "unknown"
