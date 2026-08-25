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

    `graph` is any LangGraph compiled graph (typed `Any` because its
    `astream_events` is a heavily-overloaded method a Protocol can't satisfy).
    """
    async for event in graph.astream_events(initial_state, version="v2"):
        if event["event"] != "on_chain_end":
            continue
        payload = {
            "node": event.get("name"),
            "output": event.get("data", {}).get("output"),
        }
        yield json.dumps(payload, default=str)
    yield json.dumps({"node": END_NODE, "output": None})
