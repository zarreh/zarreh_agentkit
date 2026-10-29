"""The `/healthz` liveness route every service exposed, rate-limited per route."""

from __future__ import annotations

from fastapi import APIRouter, Request
from slowapi import Limiter


def build_health_router(limiter: Limiter, rate_limit: str) -> APIRouter:
    """`GET /healthz` -> `{"status": "ok"}`, limited by `limiter` at `rate_limit`."""
    router = APIRouter(tags=["health"])

    @router.get("/healthz")
    @limiter.limit(rate_limit)
    def healthz(request: Request) -> dict[str, str]:
        return {"status": "ok"}

    return router
