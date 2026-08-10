import pytest
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.auth import EntraPrincipalMiddleware


def _client(*, required: bool = True) -> TestClient:
    app = FastAPI()

    @app.get("/api/private")
    async def private() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.websocket("/ws/private")
    async def private_ws(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_text("ok")

    app.add_middleware(EntraPrincipalMiddleware, required=required)
    return TestClient(app)


def test_missing_principal_is_rejected() -> None:
    response = _client().get("/api/private")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_easy_auth_principal_is_accepted() -> None:
    response = _client().get(
        "/api/private",
        headers={"x-ms-client-principal": "base64-encoded-claims"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_health_remains_available_for_platform_probes() -> None:
    response = _client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_websocket_principal_is_rejected() -> None:
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with _client().websocket_connect("/ws/private"):
            pass

    assert exc_info.value.code == 4401


def test_local_mode_does_not_require_principal() -> None:
    response = _client(required=False).get("/api/private")

    assert response.status_code == 200
