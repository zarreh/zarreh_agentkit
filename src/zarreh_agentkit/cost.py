"""Per-node LLM cost accounting via a LangChain callback.

LangGraph tags every node's LLM calls with `langgraph_node` in the run
metadata, so one callback attached to the whole graph invocation can attribute
each call's tokens back to the node that made it — no manual plumbing through
node code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# Approximate list pricing, USD per 1M tokens (prompt, completion). Not
# billing-grade — for the cost-meter estimate only; real prices change often.
PRICE_PER_MILLION_TOKENS: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimated USD cost of one LLM call at the approximate list price."""
    prompt_price, completion_price = PRICE_PER_MILLION_TOKENS.get(model, (0.0, 0.0))
    return (prompt_tokens * prompt_price + completion_tokens * completion_price) / 1_000_000


@dataclass
class CostEntry:
    """One attributed LLM call within a graph run."""

    node: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


class CostEntryLike(Protocol):
    """Any structurally-equivalent cost record (a consuming app's own dataclass)."""

    node: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


class CostTrackingHandler(BaseCallbackHandler):
    """Attach once per graph invocation via `config={"callbacks": [...]}`;
    `entries` accumulates one `CostEntry` per completed LLM call."""

    def __init__(self) -> None:
        self.entries: list[CostEntryLike] = []

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        metadata = kwargs.get("metadata")
        node = (
            metadata.get("langgraph_node", "unknown") if isinstance(metadata, dict) else "unknown"
        )
        llm_output = response.llm_output or {}
        usage = llm_output.get("token_usage") or {}
        model = llm_output.get("model_name", "unknown")
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        self.entries.append(
            CostEntry(
                node=node,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=estimate_cost_usd(model, prompt_tokens, completion_tokens),
            )
        )
