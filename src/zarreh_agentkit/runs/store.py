"""SQLite persistence for a run's node-by-node events and per-node LLM cost.

Every consuming service had a `RunStore` whose `run_events` / `run_costs`
tables and four accessor methods were identical; only the `runs` table --
what a run is *about* and what it produces -- differed. `RunEventLog` owns the
identical half. A service subclasses it and adds its own `runs` table, so its
existing database schema and API are unchanged.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from zarreh_agentkit.cost import CostEntry, CostEntryLike


def utc_now() -> str:
    """ISO-8601 UTC timestamp, the format every run table stores."""
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class RunEvent:
    """One persisted node step, in the same shape the SSE stream emits."""

    run_id: str
    sequence: int
    node: str
    payload_json: str
    created_at: str


class RunEventLog:
    """`<prefix>_events` and `<prefix>_costs` over one SQLite connection.

    Subclass and run your own `runs` schema on `self._conn` after
    `super().__init__`. `table_prefix` exists because one consumer names its
    tables after conversations rather than runs.
    """

    def __init__(self, db_path: Path | str, *, table_prefix: str = "run") -> None:
        if not table_prefix.isidentifier():
            raise ValueError(f"table_prefix must be an identifier, got {table_prefix!r}")
        self._events_table = f"{table_prefix}_events"
        self._costs_table = f"{table_prefix}_costs"
        # check_same_thread=False: request handlers and the background run
        # executor touch the store from different threads.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS {self._events_table} (
                run_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                node TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (run_id, sequence)
            );
            CREATE TABLE IF NOT EXISTS {self._costs_table} (
                run_id TEXT NOT NULL,
                node TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def append_event(self, run_id: str, sequence: int, node: str, payload_json: str) -> None:
        self._conn.execute(
            f"INSERT INTO {self._events_table} "
            "(run_id, sequence, node, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, sequence, node, payload_json, utc_now()),
        )
        self._conn.commit()

    def get_events(self, run_id: str, after_sequence: int = -1) -> list[RunEvent]:
        """Every event with `sequence > after_sequence`, in order -- the same
        call replays a whole run from the start (default) or tails new events
        since the last one a client already saw."""
        rows = self._conn.execute(
            f"SELECT run_id, sequence, node, payload_json, created_at FROM {self._events_table} "
            "WHERE run_id = ? AND sequence > ? ORDER BY sequence",
            (run_id, after_sequence),
        ).fetchall()
        return [
            RunEvent(
                run_id=str(row[0]),
                sequence=int(row[1]),
                node=str(row[2]),
                payload_json=str(row[3]),
                created_at=str(row[4]),
            )
            for row in rows
        ]

    def record_costs(self, run_id: str, entries: Sequence[CostEntryLike]) -> None:
        if not entries:
            return
        self._conn.executemany(
            f"INSERT INTO {self._costs_table} "
            "(run_id, node, model, prompt_tokens, completion_tokens, cost_usd) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                (run_id, e.node, e.model, e.prompt_tokens, e.completion_tokens, e.cost_usd)
                for e in entries
            ],
        )
        self._conn.commit()

    def get_costs(self, run_id: str) -> list[CostEntry]:
        rows = self._conn.execute(
            "SELECT node, model, prompt_tokens, completion_tokens, cost_usd "
            f"FROM {self._costs_table} WHERE run_id = ?",
            (run_id,),
        ).fetchall()
        return [
            CostEntry(
                node=str(row[0]),
                model=str(row[1]),
                prompt_tokens=int(row[2]),
                completion_tokens=int(row[3]),
                cost_usd=float(row[4]),
            )
            for row in rows
        ]
