from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app import public_demo_guard as guard_module
from app.api.routes_debate import (
    DEBATE_EVENTS,
    PENDING_DEBATES,
    StartDebateRequest,
    start_debate,
)
from app.api.routes_prep import (
    _PREP_CREATED_AT,
    _PREP_OWNERS,
    _PREP_QUEUES,
    _PREP_SESSIONS,
    CreatePrepSessionRequest,
    PrepMessageRequest,
    create_prep_session,
    post_prep_message,
)
from app.api.routes_session import _SESSIONS, create_session
from app.main import app
from app.public_demo_guard import (
    PublicDemoGuard,
    UsageLimitExceeded,
    client_id,
    require_admin,
)


@pytest.fixture(autouse=True)
async def reset_process_state() -> None:
    await guard_module.public_demo_guard.reset()
    _SESSIONS.clear()
    PENDING_DEBATES.clear()
    DEBATE_EVENTS.clear()
    _PREP_SESSIONS.clear()
    _PREP_QUEUES.clear()
    _PREP_OWNERS.clear()
    _PREP_CREATED_AT.clear()


@pytest.mark.asyncio
async def test_client_quota_blocks_after_limit() -> None:
    guard = PublicDemoGuard()

    await guard.consume(
        action="debate",
        client_id="client-a",
        client_limit=1,
        global_limit=10,
    )

    with pytest.raises(UsageLimitExceeded):
        await guard.consume(
            action="debate",
            client_id="client-a",
            client_limit=1,
            global_limit=10,
        )


@pytest.mark.asyncio
async def test_global_quota_applies_across_clients() -> None:
    guard = PublicDemoGuard()

    await guard.consume(
        action="debate",
        client_id="client-a",
        client_limit=10,
        global_limit=1,
    )

    with pytest.raises(UsageLimitExceeded):
        await guard.consume(
            action="debate",
            client_id="client-b",
            client_limit=10,
            global_limit=1,
        )


@pytest.mark.asyncio
async def test_model_slot_is_reusable_after_release() -> None:
    guard = PublicDemoGuard()

    await guard.acquire_model_run(client_id="client-a", client_limit=1, global_limit=1)
    with pytest.raises(UsageLimitExceeded):
        await guard.acquire_model_run(
            client_id="client-b",
            client_limit=1,
            global_limit=1,
        )

    await guard.release_model_run("client-a")
    await guard.acquire_model_run(client_id="client-b", client_limit=1, global_limit=1)


def test_client_id_ignores_untrusted_forwarded_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = type("Settings", (), {"trust_forwarded_client_ip": False})()
    monkeypatch.setattr(guard_module, "get_settings", lambda: settings)
    request = Request({
        "type": "http",
        "headers": [
            (b"x-forwarded-for", b"203.0.113.8, 10.0.0.4"),
        ],
        "client": ("10.0.0.5", 443),
    })
    direct_request = Request({
        "type": "http",
        "headers": [],
        "client": ("10.0.0.5", 443),
    })

    assert client_id(request) == client_id(direct_request)


def test_client_id_uses_forwarded_address_only_when_trusted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = type("Settings", (), {"trust_forwarded_client_ip": True})()
    monkeypatch.setattr(guard_module, "get_settings", lambda: settings)
    forwarded_request = Request({
        "type": "http",
        "headers": [
            (b"x-forwarded-for", b"203.0.113.8, 10.0.0.4"),
        ],
        "client": ("10.0.0.5", 443),
    })
    client_request = Request({
        "type": "http",
        "headers": [],
        "client": ("203.0.113.8", 443),
    })

    assert client_id(forwarded_request) == client_id(client_request)


def test_admin_token_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = type("Settings", (), {"admin_api_token": "configured-secret"})()
    monkeypatch.setattr(guard_module, "get_settings", lambda: settings)
    unauthorized = Request({
        "type": "http",
        "headers": [(b"x-admin-token", b"wrong")],
    })
    authorized = Request({
        "type": "http",
        "headers": [(b"x-admin-token", b"configured-secret")],
    })

    with pytest.raises(HTTPException) as exc_info:
        require_admin(unauthorized)
    assert exc_info.value.status_code == 401
    require_admin(authorized)


def test_admin_endpoint_is_hidden_without_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = type("Settings", (), {"admin_api_token": ""})()
    monkeypatch.setattr(guard_module, "get_settings", lambda: settings)
    request = Request({"type": "http", "headers": []})

    with pytest.raises(HTTPException) as exc_info:
        require_admin(request)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_debate_session_is_bound_to_creator() -> None:
    owner_request = Request({
        "type": "http",
        "headers": [],
        "client": ("203.0.113.8", 443),
    })
    other_request = Request({
        "type": "http",
        "headers": [],
        "client": ("203.0.113.9", 443),
    })
    session = await create_session(owner_request)
    debate = StartDebateRequest(session_id=session.session_id, question="Should we expand?")

    with pytest.raises(HTTPException) as exc_info:
        await start_debate(debate, other_request)
    assert exc_info.value.status_code == 404

    response = await start_debate(debate, owner_request)
    assert response.debate_id


@pytest.mark.asyncio
async def test_prep_session_is_bound_to_creator() -> None:
    owner_request = Request({
        "type": "http",
        "headers": [],
        "client": ("203.0.113.8", 443),
    })
    other_request = Request({
        "type": "http",
        "headers": [],
        "client": ("203.0.113.9", 443),
    })
    session = await create_prep_session(
        CreatePrepSessionRequest(role="CEO", agenda_topic="Expansion"),
        owner_request,
    )
    message = PrepMessageRequest(text="Pressure-test this", mode="coach")

    with pytest.raises(HTTPException) as exc_info:
        await post_prep_message(session.prep_session_id, message, other_request)
    assert exc_info.value.status_code == 404

    response = await post_prep_message(
        session.prep_session_id,
        message,
        owner_request,
    )
    assert response.queued is True


def test_unused_direct_delegation_route_is_not_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/prep-session/{sid}/delegate" not in paths
