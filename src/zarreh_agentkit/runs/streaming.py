"""Replay a persisted run's events, then tail it until it finishes.

The poll loop was identical across consumers; only "is the run still active"
and the terminal payload differed, so those are the one callable a consumer
supplies.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable, Sequence
from typing import Any, Protocol

from zarreh_agentkit.serialization import END_NODE


class EventLike(Protocol):
    @property
    def sequence(self) -> int: ...

    @property
    def node(self) -> str: ...

    @property
    def payload_json(self) -> str: ...


async def replay_and_tail(
    get_events: Callable[[int], Sequence[EventLike]],
    poll_end: Callable[[], dict[str, Any] | None],
    *,
    poll_interval: float = 0.25,
) -> AsyncIterator[str]:
    """One JSON `{"node", "output"}` payload per persisted event, then `__end__`.

    `get_events(after_sequence)` returns events newer than `after_sequence`
    (e.g. `functools.partial(store.get_events, run_id)`). `poll_end()` returns
    `None` while the run is still active, else the terminal `output` payload.
    Works identically whether a client connects the instant a run starts or
    reconnects long after it finished.
    """
    last_sequence = -1

    def drain() -> list[str]:
        nonlocal last_sequence
        lines = []
        for event in get_events(last_sequence):
            lines.append(json.dumps({"node": event.node, "output": json.loads(event.payload_json)}))
            last_sequence = event.sequence
        return lines

    while True:
        for line in drain():
            yield line
        end = poll_end()
        if end is not None:
            break
        await asyncio.sleep(poll_interval)

    # Events written between the drain above and the terminal status check.
    for line in drain():
        yield line
    yield json.dumps({"node": END_NODE, "output": end})
