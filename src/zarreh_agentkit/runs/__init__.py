"""Run persistence, execution and replay shared across agent services.

`store.RunEventLog` owns the events/costs half of a run store, `executor.execute_run`
the stream-persist-finalise loop, and `streaming.replay_and_tail` the SSE
replay. What a run is about, and what it produces, stays in each consumer.
"""

from zarreh_agentkit.runs.executor import RunSink, execute_run
from zarreh_agentkit.runs.store import RunEvent, RunEventLog, utc_now
from zarreh_agentkit.runs.streaming import replay_and_tail

__all__ = [
    "RunEvent",
    "RunEventLog",
    "RunSink",
    "execute_run",
    "replay_and_tail",
    "utc_now",
]
