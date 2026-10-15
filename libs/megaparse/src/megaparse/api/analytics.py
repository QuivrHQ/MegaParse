"""Server-side PostHog analytics for the MegaParse HTTP API.

The public site is this API (docs and parse endpoints), not a JavaScript
frontend, so pageviews are captured with the PostHog Python SDK.
"""

import os
import secrets
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from posthog import Posthog
from pydantic import BaseModel

DEFAULT_POSTHOG_API_KEY = "phc_vtYwGnSmVSLkgBzbtdRFoJTSzqK2sPEUZekZNbved6JV"
DEFAULT_POSTHOG_HOST = "https://us.i.posthog.com"

# Probes and the stats route are not product pageviews.
_SKIP_PAGEVIEW_PATHS = frozenset({"/healthz", "/api/stats", "/openapi.json"})

_client: Posthog | None = None


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def posthog_api_key() -> str:
    return os.environ.get("POSTHOG_API_KEY", "").strip() or DEFAULT_POSTHOG_API_KEY


def posthog_host() -> str:
    return os.environ.get("POSTHOG_HOST", "").strip() or DEFAULT_POSTHOG_HOST


def posthog_disabled() -> bool:
    # Keep pytest from shipping events to the live project.
    return _env_flag("POSTHOG_DISABLED") or "PYTEST_CURRENT_TEST" in os.environ


def build_posthog_client() -> Posthog:
    disabled = posthog_disabled()
    return Posthog(
        project_api_key=posthog_api_key(),
        host=posthog_host(),
        disabled=disabled,
        send=not disabled,
        enable_local_evaluation=False,
        enable_exception_autocapture=not disabled,
    )


def get_posthog() -> Posthog:
    global _client
    if _client is None:
        _client = build_posthog_client()
    return _client


def reset_posthog_client() -> None:
    global _client
    _client = None


def capture_event(
    event: str,
    properties: dict[str, Any] | None = None,
    distinct_id: str | None = None,
) -> None:
    """Capture a product event. Failures never affect the request."""
    try:
        payload = dict(properties or {})
        if not distinct_id:
            payload.setdefault("$process_person_profile", False)
        kwargs: dict[str, Any] = {"properties": payload}
        if distinct_id:
            kwargs["distinct_id"] = distinct_id
        get_posthog().capture(event, **kwargs)
    except Exception:
        return


def capture_exception(exc: BaseException) -> None:
    try:
        get_posthog().capture_exception(exc)
    except Exception:
        return


def _header(scope: dict[str, Any], name: bytes) -> str | None:
    for key, value in scope.get("headers") or []:
        if key.lower() == name:
            text = value.decode("latin-1").strip()
            return text or None
    return None


def _request_path(scope: dict[str, Any]) -> str:
    path = scope.get("path") or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return path


def current_url(scope: dict[str, Any]) -> str:
    scheme = scope.get("scheme") or "http"
    forwarded = _header(scope, b"x-forwarded-proto")
    if forwarded:
        scheme = forwarded.split(",")[0].strip() or scheme
    host = _header(scope, b"host") or "localhost"
    root = scope.get("root_path") or ""
    return f"{scheme}://{host}{root}{_request_path(scope)}"


def should_capture_pageview(scope: dict[str, Any]) -> bool:
    if scope.get("type") != "http" or scope.get("method") != "GET":
        return False
    return _request_path(scope) not in _SKIP_PAGEVIEW_PATHS


def capture_pageview(scope: dict[str, Any]) -> None:
    properties: dict[str, Any] = {
        "$current_url": current_url(scope),
        "$pathname": _request_path(scope),
    }
    referer = _header(scope, b"referer")
    if referer:
        properties["$referrer"] = referer
    distinct_id = _header(scope, b"x-posthog-distinct-id")
    capture_event("$pageview", properties=properties, distinct_id=distinct_id)


class PageviewMiddleware:
    """Record a PostHog ``$pageview`` for GET requests.

    Pure ASGI so upload bodies are not buffered the way ``BaseHTTPMiddleware``
    would.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        try:
            await self.app(scope, receive, send)
        finally:
            if should_capture_pageview(scope):
                capture_pageview(scope)


class UsageStats(BaseModel):
    total_users: int | None = None
    new_users_1d: int | None = None
    new_users_7d: int | None = None
    active_users_1d: int | None = None
    active_users_7d: int | None = None


def stats_authorized(authorization: str | None) -> bool:
    """True only for ``Authorization: Bearer $STATS_TOKEN``."""
    expected = os.environ.get("STATS_TOKEN", "").strip()
    if not expected or not authorization:
        return False
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.lower() != "bearer":
        return False
    token = token.strip()
    if not token:
        return False
    return secrets.compare_digest(token, expected)


def stats_payload() -> UsageStats:
    """Account metrics are unavailable: MegaParse has no user accounts."""
    return UsageStats()


def api_stats(authorization: str | None = Header(default=None)) -> UsageStats:
    if not stats_authorized(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return stats_payload()


def register_analytics(app: FastAPI) -> None:
    app.add_middleware(PageviewMiddleware)
    app.add_api_route(
        "/api/stats",
        api_stats,
        methods=["GET"],
        response_model=UsageStats,
        tags=["analytics"],
    )


@asynccontextmanager
async def analytics_lifespan(_app: FastAPI):
    try:
        get_posthog()
    except Exception:
        pass
    yield
    try:
        get_posthog().flush()
    except Exception:
        pass
