from slowapi import Limiter

from zarreh_agentkit.api.rate_limit import build_limiter, default_rate_limit
from zarreh_agentkit.settings import AgentSettings


def test_build_limiter_returns_limiter() -> None:
    assert isinstance(build_limiter(), Limiter)


def test_default_rate_limit_uses_settings() -> None:
    s = AgentSettings(rate_limit_per_minute=7)
    assert default_rate_limit(s) == "7/minute"
