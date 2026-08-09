"""Abuse controls for anonymous live-model demo traffic."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import math
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import HTTPException, Request, WebSocket

from .config import get_settings

_HOUR_SECONDS = 3600


@dataclass(frozen=True)
class UsageLimitExceeded(Exception):
    message: str
    retry_after: int


class PublicDemoGuard:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._active_by_client: dict[str, int] = defaultdict(int)
        self._active_global = 0

    async def consume(
        self,
        *,
        action: str,
        client_id: str,
        client_limit: int,
        global_limit: int,
        window_seconds: int = _HOUR_SECONDS,
    ) -> None:
        now = time.monotonic()
        async with self._lock:
            client_events = self._events[(action, client_id)]
            global_events = self._events[(action, "*")]
            self._prune(client_events, now, window_seconds)
            self._prune(global_events, now, window_seconds)

            retry_after = 1
            if len(client_events) >= client_limit:
                retry_after = max(
                    retry_after,
                    math.ceil(window_seconds - (now - client_events[0])),
                )
            if len(global_events) >= global_limit:
                retry_after = max(
                    retry_after,
                    math.ceil(window_seconds - (now - global_events[0])),
                )
            if len(client_events) >= client_limit or len(global_events) >= global_limit:
                raise UsageLimitExceeded(
                    message="Public demo usage limit reached. Try again later.",
                    retry_after=retry_after,
                )

            client_events.append(now)
            global_events.append(now)

    async def acquire_model_run(
        self,
        *,
        client_id: str,
        client_limit: int,
        global_limit: int,
    ) -> None:
        async with self._lock:
            if (
                self._active_by_client[client_id] >= client_limit
                or self._active_global >= global_limit
            ):
                raise UsageLimitExceeded(
                    message="The public demo is at capacity. Try again shortly.",
                    retry_after=15,
                )
            self._active_by_client[client_id] += 1
            self._active_global += 1

    async def release_model_run(self, client_id: str) -> None:
        async with self._lock:
            active = self._active_by_client.get(client_id, 0)
            if active > 1:
                self._active_by_client[client_id] = active - 1
            elif active == 1:
                del self._active_by_client[client_id]
            if self._active_global > 0:
                self._active_global -= 1

    async def reset(self) -> None:
        async with self._lock:
            self._events.clear()
            self._active_by_client.clear()
            self._active_global = 0

    @staticmethod
    def _prune(events: deque[float], now: float, window_seconds: int) -> None:
        cutoff = now - window_seconds
        while events and events[0] <= cutoff:
            events.popleft()


public_demo_guard = PublicDemoGuard()


def client_id(connection: Request | WebSocket) -> str:
    remote = connection.client.host if connection.client is not None else "unknown"
    if get_settings().trust_forwarded_client_ip:
        azure_client_ip = connection.headers.get("x-azure-clientip")
        forwarded_for = connection.headers.get("x-forwarded-for", "")
        forwarded_client_ip = forwarded_for.split(",")[0].strip()
        remote = azure_client_ip or forwarded_client_ip or remote
    return hashlib.sha256(remote.encode("utf-8")).hexdigest()[:24]


async def enforce_http_quota(request: Request, action: str) -> str:
    client = client_id(request)
    settings = get_settings()
    if not settings.public_demo_limits_enabled:
        return client

    limits = {
        "session": (
            settings.public_sessions_per_client_hour,
            settings.public_sessions_global_hour,
        ),
        "debate": (
            settings.public_debates_per_client_hour,
            settings.public_debates_global_hour,
        ),
        "prep_turn": (
            settings.public_prep_turns_per_client_hour,
            settings.public_prep_turns_global_hour,
        ),
    }
    client_limit, global_limit = limits[action]
    try:
        await public_demo_guard.consume(
            action=action,
            client_id=client,
            client_limit=client_limit,
            global_limit=global_limit,
        )
    except UsageLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail=exc.message,
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    return client


@asynccontextmanager
async def model_run_slot(client: str) -> AsyncIterator[None]:
    settings = get_settings()
    if not settings.public_demo_limits_enabled:
        yield
        return

    await public_demo_guard.acquire_model_run(
        client_id=client,
        client_limit=settings.public_active_runs_per_client,
        global_limit=settings.public_active_runs_global,
    )
    try:
        yield
    finally:
        await public_demo_guard.release_model_run(client)


def require_admin(request: Request) -> None:
    configured = get_settings().admin_api_token
    supplied = request.headers.get("x-admin-token", "")
    if not configured:
        raise HTTPException(status_code=404, detail="not found")
    if not hmac.compare_digest(configured, supplied):
        raise HTTPException(
            status_code=401,
            detail="administrator credentials required",
            headers={"WWW-Authenticate": "X-Admin-Token"},
        )
