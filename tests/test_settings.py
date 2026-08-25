from pydantic_settings import SettingsConfigDict

from zarreh_agentkit.settings import AgentSettings


class AppSettings(AgentSettings):
    model_config = SettingsConfigDict(env_prefix="TESTAPP_", extra="ignore")

    app_specific: str = "unset"


def test_defaults() -> None:
    s = AgentSettings()
    assert s.environment == "development"
    assert s.rate_limit_per_minute == 20
    assert s.max_request_body_bytes == 16_384


def test_subclass_env_prefix(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("TESTAPP_ENVIRONMENT", "production")
    monkeypatch.setenv("TESTAPP_APP_SPECIFIC", "hello")
    s = AppSettings()
    assert s.environment == "production"
    assert s.app_specific == "hello"
    # shared base defaults still apply
    assert s.rate_limit_per_minute == 20


def test_subclass_does_not_read_unprefixed_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ENVIRONMENT", "staging")
    s = AppSettings()
    # env_prefix isolates the subclass from the unprefixed variable
    assert s.environment != "staging"
