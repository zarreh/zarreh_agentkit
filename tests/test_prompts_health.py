from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from zarreh_agentkit.api import build_health_router, build_limiter
from zarreh_agentkit.prompts import PromptLoader


def test_prompt_loader_reads_strips_and_caches(tmp_path: Path) -> None:
    (tmp_path / "planner_v1.md").write_text("  plan carefully\n")
    loader = PromptLoader(tmp_path)
    assert loader.load("planner_v1") == "plan carefully"
    (tmp_path / "planner_v1.md").write_text("changed")
    assert loader.load("planner_v1") == "plan carefully"
    loader.cache_clear()
    assert loader.load("planner_v1") == "changed"


def test_prompt_loader_missing_id(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="nope"):
        PromptLoader(tmp_path).load("nope")


def test_health_router_is_rate_limited() -> None:
    limiter = build_limiter()
    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(build_health_router(limiter, "2/minute"))
    client = TestClient(app)
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/healthz").status_code == 200
    assert client.get("/healthz").status_code == 429
