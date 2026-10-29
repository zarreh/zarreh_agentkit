import json
from functools import partial
from pathlib import Path
from typing import Any, TypedDict

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.graph import END, StateGraph

from zarreh_agentkit.cost import CostEntry
from zarreh_agentkit.runs import RunEventLog, execute_run, replay_and_tail, utc_now
from zarreh_agentkit.serialization import END_NODE


class Store(RunEventLog):
    """A minimal consumer store: the base plus an app-owned runs table."""

    def __init__(self, db_path: Path) -> None:
        super().__init__(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, status TEXT, result TEXT)"
        )
        self.failures: list[str] = []

    def create_run(self, run_id: str) -> None:
        self._conn.execute("INSERT INTO runs VALUES (?, 'running', NULL)", (run_id,))

    def complete_run(self, run_id: str, result: str) -> None:
        self._conn.execute(
            "UPDATE runs SET status='completed', result=? WHERE id=?", (result, run_id)
        )

    def fail_run(self, run_id: str, error: str) -> None:
        self.failures.append(error)
        self._conn.execute("UPDATE runs SET status='failed', result=? WHERE id=?", (error, run_id))

    def status(self, run_id: str) -> tuple[str, str | None]:
        row = self._conn.execute("SELECT status, result FROM runs WHERE id=?", (run_id,)).fetchone()
        return str(row[0]), row[1]


@pytest.fixture
def store(tmp_path: Path) -> Store:
    s = Store(tmp_path / "runs.db")
    s.create_run("r1")
    return s


class UsageReportingChat(BaseChatModel):
    """Non-streaming fake: under `astream_events` LangChain falls back to
    `_generate`, so the message's `usage_metadata` reaches the callback intact."""

    @property
    def _llm_type(self) -> str:
        return "usage-reporting-fake"

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        message = AIMessage(
            content="ok",
            usage_metadata={"input_tokens": 1000, "output_tokens": 0, "total_tokens": 1000},
            response_metadata={"model_name": "gpt-4o-mini-2024-07-18"},
        )
        return ChatResult(generations=[ChatGeneration(message=message)])


class State(TypedDict, total=False):
    n: int
    answer: str


def _graph(model: Any = None) -> Any:
    def start(state: State) -> dict[str, int]:
        return {"n": state["n"] + 1}

    def answer(state: State) -> dict[str, str]:
        if model is None:
            return {"answer": f"n={state['n']}"}
        return {"answer": str(model.invoke("hi").content)}

    def route(state: State) -> str:
        return "answer"

    workflow = StateGraph(State)
    workflow.add_node("start", start)
    workflow.add_node("answer", answer)
    workflow.set_entry_point("start")
    workflow.add_conditional_edges("start", route, {"answer": "answer"})
    workflow.add_edge("answer", END)
    return workflow.compile()


def test_event_log_round_trip(store: Store) -> None:
    store.append_event("r1", 0, "a", '{"x": 1}')
    store.append_event("r1", 1, "b", '{"y": 2}')
    assert [e.node for e in store.get_events("r1")] == ["a", "b"]
    assert [e.sequence for e in store.get_events("r1", after_sequence=0)] == [1]
    assert store.get_events("other") == []

    store.record_costs("r1", [])
    entry = CostEntry("a", "gpt-4o", 1, 2, 0.5)
    store.record_costs("r1", [entry])
    assert store.get_costs("r1") == [entry]
    store.close()


def test_table_prefix(tmp_path: Path) -> None:
    log = RunEventLog(tmp_path / "c.db", table_prefix="conversation")
    log.append_event("c1", 0, "n", "{}")
    tables = {r[0] for r in log._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"conversation_events", "conversation_costs"} <= tables
    with pytest.raises(ValueError):
        RunEventLog(tmp_path / "x.db", table_prefix="drop table; --")


def test_utc_now_is_iso() -> None:
    assert utc_now().endswith("+00:00")


async def test_execute_run_persists_node_steps_and_finalizes(store: Store) -> None:
    def finalize(state: dict[str, Any]) -> None:
        store.complete_run("r1", state["answer"])

    await execute_run(
        run_id="r1", graph=_graph(), graph_input={"n": 1}, store=store, finalize=finalize
    )
    events = store.get_events("r1")
    assert [e.node for e in events] == ["start", "answer"]
    assert json.loads(events[1].payload_json) == {"answer": "n=2"}
    assert store.status("r1") == ("completed", "n=2")


async def test_execute_run_attributes_llm_cost_to_node(store: Store) -> None:
    model = UsageReportingChat()
    await execute_run(
        run_id="r1",
        graph=_graph(model),
        graph_input={"n": 1},
        store=store,
        finalize=lambda state: store.complete_run("r1", state["answer"]),
        node_names={"answer"},
        configurable={"thread_id": "r1"},
    )
    assert [e.node for e in store.get_events("r1")] == ["answer"]
    (cost,) = store.get_costs("r1")
    assert cost.node == "answer"
    assert cost.prompt_tokens == 1000
    assert cost.cost_usd == pytest.approx(0.00015)


async def test_execute_run_marks_failed_on_exception(store: Store) -> None:
    def finalize(state: dict[str, Any]) -> None:
        raise RuntimeError("no answer")

    await execute_run(
        run_id="r1",
        graph=_graph(),
        graph_input={"n": 1},
        store=store,
        finalize=finalize,
        sequence_start=5,
    )
    assert store.status("r1") == ("failed", "no answer")
    assert store.get_events("r1")[0].sequence == 5


async def test_replay_and_tail_replays_then_tails_until_end(store: Store) -> None:
    store.append_event("r1", 0, "a", '{"x": 1}')
    polls = 0

    def poll_end() -> dict[str, Any] | None:
        nonlocal polls
        polls += 1
        if polls == 1:
            store.append_event("r1", 1, "b", '{"y": 2}')
            return None
        # Written after the loop's last drain but before the run is seen as done.
        store.append_event("r1", 2, "c", "{}")
        return {"status": "completed"}

    lines = [
        json.loads(line)
        async for line in replay_and_tail(
            partial(store.get_events, "r1"), poll_end, poll_interval=0
        )
    ]
    assert [line["node"] for line in lines] == ["a", "b", "c", END_NODE]
    assert lines[-1]["output"] == {"status": "completed"}
