"""Defense-in-depth validation for identity headers forwarded by Easy Auth."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]


class EntraPrincipalMiddleware:
    def __init__(self, app: Callable[..., Awaitable[None]], *, required: bool) -> None:
        self.app = app
        self.required = required

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            not self.required
            or scope["type"] not in {"http", "websocket"}
            or scope.get("path") == "/health"
        ):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        if headers.get(b"x-ms-client-principal"):
            await self.app(scope, receive, send)
            return

        if scope["type"] == "websocket":
            await send(
                {
                    "type": "websocket.close",
                    "code": 4401,
                    "reason": "Authentication required",
                }
            )
            return

        body = b'{"detail":"Authentication required"}'
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
