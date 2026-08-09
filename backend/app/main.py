"""FastAPI entrypoint (§7.1)."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    routes_audience,
    routes_debate,
    routes_prep,
    routes_session,
    routes_swap,
    ws_prep,
    ws_stream,
)
from .config import get_settings
from .public_demo_guard import require_admin
from .telemetry import configure_telemetry, get_logger

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    settings = get_settings()
    configure_telemetry(settings.appinsights_connection_string)
    log.info("startup", models=settings.model_registry(), fake=settings.use_fake_debate)

    # Probe-on-start: best-effort, never blocks startup.
    try:
        from .agents.model_router import probe_all

        await probe_all()
    except Exception as e:  # noqa: BLE001
        log.warning("router_probe_failed", error=str(e))

    yield


app = FastAPI(title="Frontier Boardroom", version="0.1.0", lifespan=lifespan)
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_session.router, prefix="/api/v1")
app.include_router(routes_debate.router, prefix="/api/v1")
app.include_router(routes_prep.router, prefix="/api/v1")
app.include_router(routes_swap.router, prefix="/api/v1")
app.include_router(routes_audience.router, prefix="/api/v1")
app.include_router(ws_stream.router)
app.include_router(ws_prep.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/dev/router-probe")
async def router_probe(request: Request) -> dict:
    require_admin(request)
    from .agents.model_router import probe_all

    return await probe_all()


@app.get("/dev/fake-debate")
async def fake_debate() -> dict:
    fixture = Path(__file__).parent / "dev" / "fake_debate.json"
    if not fixture.exists():
        return {"error": "fixture missing", "path": str(fixture)}
    return json.loads(fixture.read_text(encoding="utf-8"))
