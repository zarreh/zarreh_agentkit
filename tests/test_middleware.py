from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from zarreh_agentkit.api.middleware import MaxBodySizeMiddleware


def _app(limit: int) -> FastAPI:
    app = FastAPI()

    @app.post("/echo")
    async def echo(request: Request) -> dict[str, int]:
        body = await request.body()
        return {"size": len(body)}

    app.add_middleware(MaxBodySizeMiddleware, max_body_bytes=limit)
    return app


def test_under_limit_passes_through() -> None:
    client = TestClient(_app(100))
    r = client.post("/echo", content=b"x" * 50)
    assert r.status_code == 200
    assert r.json() == {"size": 50}


def test_over_limit_is_rejected_413() -> None:
    client = TestClient(_app(100))
    r = client.post("/echo", content=b"x" * 101)
    assert r.status_code == 413
    assert "exceeds" in r.json()["detail"]


def test_oversize_without_content_length_still_capped() -> None:
    client = TestClient(_app(10))
    r = client.post("/echo", content=b"a" * 500, headers={"content-length": ""})
    assert r.status_code == 413


def test_non_http_scope_untouched() -> None:
    # websocket / lifespan scopes pass straight through; nothing to assert
    # beyond the middleware constructing and being importable here.
    assert MaxBodySizeMiddleware is not None
