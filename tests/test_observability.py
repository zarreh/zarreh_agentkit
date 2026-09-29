from collections.abc import MutableMapping
from typing import Any

import structlog

from zarreh_agentkit.observability import (
    _add_correlation_id,
    build_tracing_callbacks,
    configure_logging,
    correlation_id,
    get_logger,
)


def test_configure_logging_development() -> None:
    configure_logging("development")
    assert structlog.is_configured()


def test_configure_logging_production() -> None:
    configure_logging("production")
    assert structlog.is_configured()


def test_get_logger_emits_a_record() -> None:
    configure_logging("development")
    get_logger("test").info("hello")  # must not raise


def test_extra_processors_run_on_the_assembled_event_just_before_the_renderer() -> None:
    seen: list[dict[str, object]] = []

    def redact(logger: Any, method: str, event_dict: MutableMapping[str, Any]) -> Any:
        seen.append(dict(event_dict))
        event_dict["secret"] = "[redacted]"
        return event_dict

    rendered: list[str] = []

    def capture(logger: Any, method: str, event_dict: MutableMapping[str, Any]) -> str:
        rendered.append(str(event_dict))
        return ""

    configure_logging("production", extra_processors=[redact])
    structlog.configure(
        processors=[*structlog.get_config()["processors"][:-1], capture],
    )
    get_logger("test").info("hello", secret="hunter2")

    # The redactor saw the fully assembled event (level and timestamp already
    # added) and its edit is what reached the renderer.
    assert seen[0]["secret"] == "hunter2"
    assert "level" in seen[0] and "timestamp" in seen[0]
    assert "[redacted]" in rendered[0] and "hunter2" not in rendered[0]


def test_correlation_id_injected_into_event_dict() -> None:
    event_dict: dict[str, object] = {}
    token = correlation_id.set("req-123")
    try:
        result = _add_correlation_id(None, "info", event_dict)
    finally:
        correlation_id.reset(token)
    assert result["correlation_id"] == "req-123"


def test_correlation_id_absent_leaves_event_dict_untouched() -> None:
    event_dict: dict[str, object] = {"event": "hello"}
    result = _add_correlation_id(None, "info", event_dict)
    assert "correlation_id" not in result


def test_build_tracing_callbacks_empty_when_no_api_key() -> None:
    assert build_tracing_callbacks("", "some-project") == []


def test_build_tracing_callbacks_returns_tracer_when_configured() -> None:
    from langchain_core.tracers.langchain import LangChainTracer

    callbacks = build_tracing_callbacks("lsv2_fake_key", "some-project")
    assert len(callbacks) == 1
    tracer = callbacks[0]
    assert isinstance(tracer, LangChainTracer)
    assert tracer.project_name == "some-project"
