"""Structured logging, per-request correlation IDs, and dual tracing.

The `configure_logging`/`get_logger` pair was byte-identical in both services,
so it is lifted verbatim. `correlation_id` is the single shared `ContextVar`
every service stamps onto its log records and its traces.

`build_tracing_callbacks` was independently reimplemented, byte-for-byte
identical, in three consuming services before landing here — the clearest
possible case for extraction.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

import structlog
from langchain_core.callbacks.base import BaseCallbackHandler

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


def build_tracing_callbacks(
    langsmith_api_key: str, langsmith_project: str
) -> list[BaseCallbackHandler]:
    """A `LangChainTracer` callback if LangSmith is configured, else none.

    Takes plain values rather than a settings object so it has no dependency
    on any consuming service's settings shape. LangSmith itself reads the
    API key from the ambient environment; the key is accepted here only to
    gate whether tracing is attached at all.
    """
    if not langsmith_api_key:
        return []
    from langchain_core.tracers.langchain import LangChainTracer

    return [LangChainTracer(project_name=langsmith_project)]
