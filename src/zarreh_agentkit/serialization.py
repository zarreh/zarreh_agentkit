"""Bridge a LangGraph run to Server-Sent Events, one event per node step.

The "project a graph run into a streamable, typed API payload" shape was the
same in both services. This is the contract X3's frontend types against.

`iter_node_outputs` is the node-boundary filter every consumer's run executor
had reimplemented; `stream_graph_events` and `zarreh_agentkit.runs` build on it.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Collection, Mapping
from typing import Any

from pydantic import BaseModel

END_NODE = "__end__"


def json_default(value: object) -> object:
    """`json.dumps(..., default=json_default)`: Pydantic models as JSON-mode
    dicts, anything else as its `str`."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return str(value)


async def iter_node_outputs(
    graph: Any,
    graph_input: Any,
    *,
    config: Mapping[str, Any] | None = None,
    node_names: Collection[str] | None = None,
) -> AsyncIterator[tuple[str, Any]]:
    """`(node, output)` for every completed node step of one graph run.

    A step is a genuine node boundary: `name == metadata["langgraph_node"]`.
    Presence of `langgraph_node` alone is not enough -- a conditional-edge
    routing function also emits `on_chain_end` with its *source* node in the
    metadata, under its own function name, and the graph itself emits one with
    no node at all. `node_names`, if given, further restricts to that set.

    `graph` is any LangGraph compiled graph (typed `Any` because its
    `astream_events` is a heavily-overloaded method a Protocol can't satisfy).
    """
    kwargs: dict[str, Any] = {"version": "v2"}
    if config is not None:
        kwargs["config"] = config
    async for event in graph.astream_events(graph_input, **kwargs):
        if event["event"] != "on_chain_end":
            continue
        node = (event.get("metadata") or {}).get("langgraph_node")
        if not node or event.get("name") != node:
            continue
        if node_names is not None and node not in node_names:
            continue
        yield node, (event.get("data") or {}).get("output")


async def stream_graph_events(graph: Any, initial_state: Any) -> AsyncIterator[str]:
    """One SSE `data:` payload per completed node step, then a terminal event."""
    async for node, output in iter_node_outputs(graph, initial_state):
        yield json.dumps({"node": node, "output": output}, default=str)
    yield json.dumps({"node": END_NODE, "output": None})
