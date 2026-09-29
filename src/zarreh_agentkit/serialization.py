"""Bridge a LangGraph run to Server-Sent Events, one event per node step.

The "project a graph run into a streamable, typed API payload" shape was the
same in both services. This is the contract X3's frontend types against.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

END_NODE = "__end__"


async def stream_graph_events(graph: Any, initial_state: Any) -> AsyncIterator[str]:
    """One SSE `data:` payload per completed node step, then a terminal event.

    A step is a genuine node boundary: `name == metadata["langgraph_node"]`.
    Presence of `langgraph_node` alone is not enough -- a conditional-edge
    routing function also emits `on_chain_end` with its *source* node in the
    metadata, under its own function name, and the graph itself emits one with
    no node at all. Both would otherwise surface as spurious steps.

    `graph` is any LangGraph compiled graph (typed `Any` because its
    `astream_events` is a heavily-overloaded method a Protocol can't satisfy).
    """
    async for event in graph.astream_events(initial_state, version="v2"):
        if event["event"] != "on_chain_end":
            continue
        node = (event.get("metadata") or {}).get("langgraph_node")
        if not node or event.get("name") != node:
            continue
        payload = {
            "node": node,
            "output": event.get("data", {}).get("output"),
        }
        yield json.dumps(payload, default=str)
    yield json.dumps({"node": END_NODE, "output": None})
