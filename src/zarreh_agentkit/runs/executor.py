"""Run one LangGraph invocation to completion, persisting as it goes.

Every consuming service's `run_executor` had the same body: bind the
correlation id, attach cost + tracing callbacks, stream node steps into the
store, record per-node cost, hand the merged final state to an app-specific
finaliser, and mark the run failed on any exception. That body lives here;
the initial state, the node set and what "finished" means stay in the app.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Collection, Mapping, Sequence
from typing import Any, Protocol

import structlog
from langchain_core.callbacks.base import BaseCallbackHandler

from zarreh_agentkit.cost import CostEntryLike, CostTrackingHandler
from zarreh_agentkit.observability import get_logger
from zarreh_agentkit.serialization import iter_node_outputs, json_default

logger = get_logger(__name__)


class RunSink(Protocol):
    """What `execute_run` writes to -- a `RunEventLog` subclass with a `fail_run`."""

    def append_event(self, run_id: str, sequence: int, node: str, payload_json: str) -> None: ...

    def record_costs(self, run_id: str, entries: Sequence[CostEntryLike]) -> None: ...

    def fail_run(self, run_id: str, error: str) -> None: ...


async def execute_run(
    *,
    run_id: str,
    graph: Any,
    graph_input: Any,
    store: RunSink,
    finalize: Callable[[dict[str, Any]], None],
    callbacks: Sequence[BaseCallbackHandler] = (),
    node_names: Collection[str] | None = None,
    configurable: Mapping[str, Any] | None = None,
    sequence_start: int = 0,
) -> None:
    """Stream `graph` on `graph_input`, persisting each node step to `store`.

    Every node step is stored (its output JSON-encoded); dict outputs are also
    merged, in order, into the final state passed to `finalize`, which decides
    how the run completes (e.g. `store.complete_run(...)` or `store.fail_run(...)`).
    Per-node LLM cost is recorded before `finalize` runs. Any exception --
    from the graph or from `finalize` -- marks the run failed and is not
    re-raised: this runs as a background task with no caller to report to.

    `callbacks` are extra handlers (typically `build_tracing_callbacks(...)`);
    a `CostTrackingHandler` is always attached.
    """
    structlog.contextvars.bind_contextvars(correlation_id=run_id)
    try:
        cost_handler = CostTrackingHandler()
        config: dict[str, Any] = {
            "callbacks": [cost_handler, *callbacks],
            "metadata": {"correlation_id": run_id},
        }
        if configurable is not None:
            config["configurable"] = dict(configurable)
        final_state: dict[str, Any] = {}
        sequence = sequence_start

        async for node, output in iter_node_outputs(
            graph, graph_input, config=config, node_names=node_names
        ):
            if isinstance(output, dict):
                final_state.update(output)
            store.append_event(run_id, sequence, node, json.dumps(output, default=json_default))
            sequence += 1

        store.record_costs(run_id, cost_handler.entries)
        finalize(final_state)
    except Exception as exc:
        logger.exception("run_failed", run_id=run_id)
        store.fail_run(run_id, str(exc))
    finally:
        structlog.contextvars.unbind_contextvars("correlation_id")
