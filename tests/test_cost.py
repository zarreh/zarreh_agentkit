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


def test_dated_model_prices_as_its_family() -> None:
    assert estimate_cost_usd("gpt-4o-mini-2024-07-18", 1_000_000, 0) == 0.15
    assert estimate_cost_usd("gpt-4o-2024-08-06", 1_000_000, 0) == 2.50
    assert estimate_cost_usd("gpt-4omni", 1_000_000, 0) == 0.0


def test_node_is_read_from_the_start_event() -> None:
    import uuid

    handler = CostTrackingHandler()
    run_id = uuid.uuid4()
    handler.on_chat_model_start({}, [[]], run_id=run_id, metadata={"langgraph_node": "draft"})
    result = LLMResult(
        generations=[[]],
        llm_output={
            "model_name": "gpt-4o",
            "token_usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
    )
    handler.on_llm_end(result, run_id=run_id)
    assert handler.entries[0].node == "draft"


def test_llm_start_also_records_node() -> None:
    import uuid

    handler = CostTrackingHandler()
    run_id = uuid.uuid4()
    handler.on_llm_start({}, ["p"], run_id=run_id, metadata={"langgraph_node": "plan"})
    handler.on_llm_end(LLMResult(generations=[[]], llm_output=None), run_id=run_id)
    assert handler.entries[0].node == "plan"


def test_usage_metadata_fallback_for_structured_output() -> None:
    import uuid

    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration

    message = AIMessage(
        content="",
        usage_metadata={"input_tokens": 200, "output_tokens": 40, "total_tokens": 240},
        response_metadata={"model_name": "gpt-4o-mini-2024-07-18"},
    )
    result = LLMResult(generations=[[ChatGeneration(message=message)]], llm_output=None)
    handler = CostTrackingHandler()
    handler.on_llm_end(result, run_id=uuid.uuid4())
    entry = handler.entries[0]
    assert entry.model == "gpt-4o-mini-2024-07-18"
    assert (entry.prompt_tokens, entry.completion_tokens) == (200, 40)
    assert entry.cost_usd == estimate_cost_usd("gpt-4o-mini", 200, 40)


def test_no_usage_anywhere_is_zero() -> None:
    import uuid

    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration

    result = LLMResult(
        generations=[[ChatGeneration(message=AIMessage(content="x"))]], llm_output=None
    )
    handler = CostTrackingHandler()
    handler.on_llm_end(result, run_id=uuid.uuid4())
    assert handler.entries[0].cost_usd == 0.0
