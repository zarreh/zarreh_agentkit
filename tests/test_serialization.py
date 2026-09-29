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


def _node_end(name: str, output: dict[str, Any]) -> dict[str, Any]:
    return {
        "event": "on_chain_end",
        "name": name,
        "metadata": {"langgraph_node": name},
        "data": {"output": output},
    }


async def test_emits_one_payload_per_chain_end() -> None:
    graph = FakeGraph(
        [
            _node_end("planner", {"plan": 1}),
            {"event": "on_llm_start", "name": "ignored"},
            _node_end("writer", {"done": True}),
        ]
    )
    events = await _collect(graph)
    assert events[0] == {"node": "planner", "output": {"plan": 1}}
    assert events[1] == {"node": "writer", "output": {"done": True}}
    # terminal sentinel always last
    assert events[-1] == {"node": END_NODE, "output": None}


async def test_routing_function_events_are_not_steps() -> None:
    # A conditional-edge router reports its *source* node in metadata but its own
    # function name as the event name.
    graph = FakeGraph(
        [
            _node_end("investigate", {"n": 1}),
            {
                "event": "on_chain_end",
                "name": "route_after_investigate",
                "metadata": {"langgraph_node": "investigate"},
                "data": {"output": "draft_answer"},
            },
        ]
    )
    events = await _collect(graph)
    assert [e["node"] for e in events] == ["investigate", END_NODE]


async def test_graph_level_and_metadata_less_events_are_not_steps() -> None:
    graph = FakeGraph(
        [
            {"event": "on_chain_end", "name": "LangGraph", "data": {"output": {}}},
            {
                "event": "on_chain_end",
                "name": "RunnableSequence",
                "metadata": {},
                "data": {"output": {}},
            },
        ]
    )
    events = await _collect(graph)
    assert events == [{"node": END_NODE, "output": None}]


async def test_non_chain_end_events_are_skipped() -> None:
    graph = FakeGraph([{"event": "on_tool_start", "name": "t", "data": {}}])
    events = await _collect(graph)
    assert events == [{"node": END_NODE, "output": None}]


async def test_real_graph_with_conditional_edge_yields_only_node_steps() -> None:
    # Against real LangGraph output rather than hand-built events: the router
    # below emits its own on_chain_end that must not surface as a step.
    from typing import TypedDict

    from langgraph.graph import END, StateGraph

    class State(TypedDict):
        n: int

    def start(state: State) -> dict[str, int]:
        return {"n": state["n"] + 1}

    def finish(state: State) -> dict[str, int]:
        return {"n": state["n"] * 10}

    def route(state: State) -> str:
        return "finish"

    workflow = StateGraph(State)
    workflow.add_node("start", start)
    workflow.add_node("finish", finish)
    workflow.set_entry_point("start")
    workflow.add_conditional_edges("start", route, {"finish": "finish"})
    workflow.add_edge("finish", END)

    lines = [line async for line in stream_graph_events(workflow.compile(), {"n": 1})]
    assert [json.loads(line)["node"] for line in lines] == ["start", "finish", END_NODE]
