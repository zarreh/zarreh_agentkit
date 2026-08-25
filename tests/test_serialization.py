import json
from collections.abc import AsyncIterator
from typing import Any

from zarreh_agentkit.serialization import END_NODE, stream_graph_events


class FakeGraph:
    """Emits the same `astream_events` shape LangGraph produces."""

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self._events = events

    async def astream_events(
        self, initial_state: Any, *, version: str
    ) -> AsyncIterator[dict[str, Any]]:
        assert version == "v2"
        for e in self._events:
            yield e


async def _collect(graph: FakeGraph) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    async for line in stream_graph_events(graph, {}):
        out.append(json.loads(line))
    return out


async def test_emits_one_payload_per_chain_end() -> None:
    graph = FakeGraph(
        [
            {"event": "on_chain_end", "name": "planner", "data": {"output": {"plan": 1}}},
            {"event": "on_llm_start", "name": "ignored"},
            {"event": "on_chain_end", "name": "writer", "data": {"output": {"done": True}}},
        ]
    )
    events = await _collect(graph)
    assert events[0] == {"node": "planner", "output": {"plan": 1}}
    assert events[1] == {"node": "writer", "output": {"done": True}}
    # terminal sentinel always last
    assert events[-1] == {"node": END_NODE, "output": None}


async def test_non_chain_end_events_are_skipped() -> None:
    graph = FakeGraph([{"event": "on_tool_start", "name": "t", "data": {}}])
    events = await _collect(graph)
    assert events == [{"node": END_NODE, "output": None}]
