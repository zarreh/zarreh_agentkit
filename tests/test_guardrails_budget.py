import time

from langchain_core.messages import AIMessage, HumanMessage, ToolCall

from zarreh_agentkit.guardrails.budget import Budget, budget_breach_reason, count_tool_calls


def _tool_call(name: str) -> ToolCall:
    return {"name": name, "args": {}, "id": name}


def test_count_tool_calls_sums_across_ai_messages() -> None:
    messages = [
        HumanMessage(content="hi"),
        AIMessage(content="", tool_calls=[_tool_call("a"), _tool_call("b")]),
        AIMessage(content="final"),
        AIMessage(content="", tool_calls=[_tool_call("c")]),
    ]
    assert count_tool_calls(messages) == 3


def test_within_budget_returns_none() -> None:
    budget = Budget(max_tool_calls=5, max_wall_clock_seconds=60.0)
    assert budget_breach_reason(3, time.time(), budget) is None


def test_exceeding_tool_calls_reports_reason() -> None:
    budget = Budget(max_tool_calls=5, max_wall_clock_seconds=60.0)
    reason = budget_breach_reason(6, time.time(), budget)
    assert reason is not None
    assert "max_tool_calls=5" in reason


def test_exceeding_wall_clock_reports_reason() -> None:
    budget = Budget(max_tool_calls=5, max_wall_clock_seconds=0.01)
    started_at = time.time() - 1.0
    reason = budget_breach_reason(0, started_at, budget)
    assert reason is not None
    assert "max_wall_clock_seconds=0.01" in reason


def test_default_budget_has_sane_ceilings() -> None:
    budget = Budget()
    assert budget.max_tool_calls == 15
    assert budget.max_wall_clock_seconds == 120.0
