"""Structured logging and per-request correlation IDs.

The `configure_logging`/`get_logger` pair was byte-identical in both services,
so it is lifted verbatim. `correlation_id` is the single shared `ContextVar`
every service stamps onto its log records and its traces.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

import structlog

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def _add_correlation_id(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    if correlation_id.get():
        event_dict["correlation_id"] = correlation_id.get()
    return event_dict


def configure_logging(environment: str) -> None:
    """Configure structlog: pretty console in dev, JSON in production."""
    renderer = (
        structlog.dev.ConsoleRenderer()
        if environment == "development"
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_correlation_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]
