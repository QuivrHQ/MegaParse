"""PostHog pageviews and the read-only /api/stats endpoint.

Loaded without the package ``__init__`` so the suite does not pull the parser
runtime. Run with ``pytest --noconftest`` when the parser extras are absent.
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_ANALYTICS_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "megaparse" / "api" / "analytics.py"
)


def _load_analytics():
    spec = importlib.util.spec_from_file_location(
        "megaparse_api_analytics", _ANALYTICS_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _Recorder:
    def __init__(self, raise_on_capture: bool = False):
        self.events = []
        self.raise_on_capture = raise_on_capture
        self.flushed = False

    def capture(self, event, **kwargs):
        if self.raise_on_capture:
            raise RuntimeError("analytics down")
        self.events.append((event, kwargs))

    def capture_exception(self, exc, **kwargs):
        if self.raise_on_capture:
            raise RuntimeError("analytics down")
        self.events.append(("exception", {"exc": exc, **kwargs}))

    def flush(self):
        self.flushed = True


@pytest.fixture
def analytics(monkeypatch):
    module = _load_analytics()
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
    monkeypatch.delenv("POSTHOG_HOST", raising=False)
    monkeypatch.delenv("STATS_TOKEN", raising=False)
    module.reset_posthog_client()
    return module


def _client(analytics, recorder: _Recorder) -> TestClient:
    analytics.get_posthog = lambda: recorder
    app = FastAPI(lifespan=analytics.analytics_lifespan)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/guide")
    def guide():
        return {"ok": True}

    @app.post("/v1/echo")
    async def echo(payload: dict):
        return payload

    analytics.register_analytics(app)
    return TestClient(app)


def test_client_defaults_to_public_project(analytics, monkeypatch):
    monkeypatch.setenv("POSTHOG_DISABLED", "true")
    client = analytics.build_posthog_client()
    assert client.api_key == "phc_vtYwGnSmVSLkgBzbtdRFoJTSzqK2sPEUZekZNbved6JV"
    assert client.host == "https://us.i.posthog.com"
    assert client.disabled is True


def test_client_uses_env_override(analytics, monkeypatch):
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_override")
    monkeypatch.setenv("POSTHOG_HOST", "https://us.i.posthog.com")
    monkeypatch.setenv("POSTHOG_DISABLED", "true")
    client = analytics.build_posthog_client()
    assert client.api_key == "phc_override"
    assert client.host == "https://us.i.posthog.com"


def test_pageview_captured_for_get(analytics):
    recorder = _Recorder()
    with _client(analytics, recorder) as client:
        response = client.get(
            "/guide", headers={"referer": "https://megaparse.com/"}
        )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert recorder.flushed is True
    assert len(recorder.events) == 1
    event, kwargs = recorder.events[0]
    assert event == "$pageview"
    assert kwargs["properties"]["$pathname"] == "/guide"
    assert kwargs["properties"]["$current_url"] == "http://testserver/guide"
    assert kwargs["properties"]["$referrer"] == "https://megaparse.com/"
    assert kwargs["properties"]["$process_person_profile"] is False
    assert "distinct_id" not in kwargs


def test_pageview_uses_distinct_id_header(analytics):
    recorder = _Recorder()
    with _client(analytics, recorder) as client:
        response = client.get(
            "/guide", headers={"x-posthog-distinct-id": "user-7"}
        )
    assert response.status_code == 200
    event, kwargs = recorder.events[0]
    assert event == "$pageview"
    assert kwargs["distinct_id"] == "user-7"
    assert "$process_person_profile" not in kwargs["properties"]


def test_swagger_docs_count_as_pageviews(analytics):
    recorder = _Recorder()
    with _client(analytics, recorder) as client:
        response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text
    assert [event for event, _ in recorder.events] == ["$pageview"]
    assert recorder.events[0][1]["properties"]["$pathname"] == "/docs"


def test_skips_health_stats_and_non_get(analytics, monkeypatch):
    monkeypatch.setenv("STATS_TOKEN", "stats-secret")
    recorder = _Recorder()
    with _client(analytics, recorder) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/openapi.json").status_code == 200
        stats = client.get(
            "/api/stats", headers={"Authorization": "Bearer stats-secret"}
        )
        echo = client.post("/v1/echo", json={"hello": "world"})
    assert stats.status_code == 200
    assert echo.status_code == 200
    assert echo.json() == {"hello": "world"}
    assert recorder.events == []


def test_stats_requires_bearer_token(analytics, monkeypatch):
    monkeypatch.setenv("STATS_TOKEN", "stats-secret")
    recorder = _Recorder()
    with _client(analytics, recorder) as client:
        missing = client.get("/api/stats")
        wrong = client.get("/api/stats", headers={"Authorization": "Bearer nope"})
        basic = client.get("/api/stats", headers={"Authorization": "Basic stats-secret"})
        ok = client.get(
            "/api/stats", headers={"Authorization": "bearer stats-secret"}
        )
        method = client.post(
            "/api/stats", headers={"Authorization": "Bearer stats-secret"}
        )
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert basic.status_code == 401
    assert ok.status_code == 200
    assert ok.json() == {
        "total_users": None,
        "new_users_1d": None,
        "new_users_7d": None,
        "active_users_1d": None,
        "active_users_7d": None,
    }
    assert method.status_code == 405


def test_stats_closed_when_token_unset(analytics, monkeypatch):
    monkeypatch.delenv("STATS_TOKEN", raising=False)
    recorder = _Recorder()
    with _client(analytics, recorder) as client:
        response = client.get("/api/stats", headers={"Authorization": "Bearer anything"})
    assert response.status_code == 401


def test_analytics_failure_does_not_break_response(analytics):
    recorder = _Recorder(raise_on_capture=True)
    with _client(analytics, recorder) as client:
        response = client.get("/guide")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
