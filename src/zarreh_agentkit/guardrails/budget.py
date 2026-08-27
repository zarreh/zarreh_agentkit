"""Per-run resource-limit guardrail (tool calls, wall clock).

Two consuming services each built this independently, converging on an
identical `Budget` shape and breach check but differing in one place: the
*ceiling* is shared, the *response to a breach* is not — one service ends
the run with an "incomplete" finding, another with a conservative templated
answer. This module owns the ceiling only; each service decides what a
breach means for its own users.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage


@dataclass(frozen=True)
class Budget:
    max_tool_calls: int = 15
    max_wall_clock_seconds: float = 120.0


DEFAULT_BUDGET = Budget()


def count_tool_calls(messages: Sequence[BaseMessage]) -> int:
    """Number of tool calls issued across a LangChain message history."""
    return sum(len(m.tool_calls) for m in messages if isinstance(m, AIMessage) and m.tool_calls)


def budget_breach_reason(
    tool_call_count: int, started_at: float, budget: Budget = DEFAULT_BUDGET
) -> str | None:
    """A human-readable breach reason, or None if within budget.

    Takes an already-computed `tool_call_count` rather than a message
    history so it has no dependency on how a given service tracks calls —
    use `count_tool_calls` to derive it from a LangChain message history,
    or count some other way.
    """
    if tool_call_count > budget.max_tool_calls:
        return f"exceeded max_tool_calls={budget.max_tool_calls} (used {tool_call_count})"
    elapsed = time.time() - started_at
    if elapsed > budget.max_wall_clock_seconds:
        return (
            f"exceeded max_wall_clock_seconds={budget.max_wall_clock_seconds} "
            f"(elapsed {elapsed:.1f}s)"
        )
    return None
