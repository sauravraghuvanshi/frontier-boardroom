"""Replicate the exact frontend flow with Origin/CORS headers — proves the
live Prep page should work end-to-end if the deployed bundle matches the
sources."""
import asyncio
import json
import sys
import urllib.request
import websockets

API = "https://app-frontier-prod-backend.azurewebsites.net"
WS = "wss://app-frontier-prod-backend.azurewebsites.net"
ORIGIN = "https://app-frontier-prod-frontend.azurewebsites.net"


def post_json(path: str, body: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode(),
        headers={
            "content-type": "application/json",
            "origin": ORIGIN,
            "referer": ORIGIN + "/prep",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()}


async def main():
    # Step 1: replicate seat=CEO, agenda=sea-expansion ("Q1 2026 expansion: SEA vs double-down India")
    code, sess = post_json(
        "/api/v1/prep-session",
        {
            "role": "CEO",
            "agenda_topic": "Q1 2026 expansion: SEA vs double-down India",
            "agenda_id": "sea-expansion",
        },
    )
    print(f"[POST /prep-session] {code} {sess}", flush=True)
    if code != 200:
        sys.exit(1)
    sid = sess["prep_session_id"]

    # Step 2: open WS WITHOUT awaiting onopen (mirrors usePrepStream.ts), then
    # immediately POST /message — the race the browser hits.
    async def open_ws():
        return await websockets.connect(
            f"{WS}/ws/prep/{sid}",
            ping_interval=None,
            origin=ORIGIN,
        )

    ws_task = asyncio.create_task(open_ws())

    code, msg_resp = post_json(
        f"/api/v1/prep-session/{sid}/message",
        {"text": "Help me defend the SEA expansion plan", "mode": "coach", "simulate_role": None},
    )
    print(f"[POST /message] {code} {msg_resp}", flush=True)

    ws = await ws_task
    print("[ws] connected", flush=True)
    try:
        first = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
        print(f"  -> {first}", flush=True)
        assert first["type"] == "prep_ready"

        chars = 0
        agent = None
        cites = 0
        text_buf = []
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=120)
            except asyncio.TimeoutError:
                print("TIMEOUT waiting for turn_end", flush=True)
                sys.exit(1)
            evt = json.loads(raw)
            t = evt.get("type")
            if t == "user_message":
                print(f"  user_message: {evt.get('text')[:60]}", flush=True)
            elif t == "turn_start":
                agent = evt["agent"]
                print(f"  turn_start: {agent} {evt.get('model')}", flush=True)
            elif t == "citation":
                cites += 1
            elif t == "token":
                chars += len(evt.get("text", ""))
                text_buf.append(evt.get("text", ""))
            elif t == "turn_end":
                full = "".join(text_buf)
                print(f"  turn_end: {chars} chars, {cites} cites", flush=True)
                print(f"  FULL_TEXT: {full!r}", flush=True)
                break
            elif t == "error":
                print(f"  ERROR: {evt}", flush=True)
                sys.exit(1)
    finally:
        await ws.close()

    if chars < 50 or agent != "CEO":
        print(f"FAIL: chars={chars} agent={agent}")
        sys.exit(1)
    print("PASS: live browser-style flow streams CEO coach reply end-to-end")


asyncio.run(main())
