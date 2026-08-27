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
