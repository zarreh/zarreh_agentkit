"""A single shared slowapi `Limiter`, applied per-route.

Applied per-route via the decorator, not `SlowAPIMiddleware`'s automatic
default-limits-for-everything: the middleware walks `app.routes` looking for
plain `APIRoute` objects with `.endpoint`, but FastAPI's `include_router` now
wraps included routers in an internal `_IncludedRouter` mount that has no
`.endpoint` — so the middleware silently finds no handler and treats every
route as exempt. Confirmed directly: the decorator form works with
`include_router`, the middleware form does not.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from zarreh_agentkit.settings import AgentSettings


def build_limiter() -> Limiter:
    """One `Limiter` per application, keyed on the remote address."""
    return Limiter(key_func=get_remote_address)


def default_rate_limit(settings: AgentSettings) -> str:
    """The slowapi limit string for the app's configured per-minute rate."""
    return f"{settings.rate_limit_per_minute}/minute"
