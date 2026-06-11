"""Live E2E prep smoke. Points at deployed backend."""
import asyncio
import json
import sys
import urllib.request
import websockets

API = "https://app-frontier-prod-backend.azurewebsites.net"
WS = "wss://app-frontier-prod-backend.azurewebsites.net"


def post_json(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


async def collect_turn(ws, label: str) -> dict:
    text_chunks: list[str] = []
    cites: list[dict] = []
    agent: str | None = None
    model: str | None = None
    print(f"\n=== {label} ===", flush=True)
    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=120)
        except asyncio.TimeoutError:
            print(f"  TIMEOUT on {label}", flush=True)
            return {"agent": agent, "text": "".join(text_chunks), "cites": cites, "ok": False}
        evt = json.loads(raw)
        et = evt.get("type")
        if et == "user_message":
            print(f"  [user] {evt.get('text', '')[:80]} (mode={evt.get('mode')})", flush=True)
        elif et == "turn_start":
            agent = evt["agent"]
            model = evt["model"]
            print(f"  [turn_start] agent={agent} model={model}", flush=True)
        elif et == "citation":
            cites.append(evt)
            uri = evt.get("source_uri", "?")
            tail = uri.split('/')[-1] if uri else "?"
            print(f"  [citation] {tail} {evt.get('confidence', 0):.2f}", flush=True)
        elif et == "token":
            text_chunks.append(evt.get("text", ""))
        elif et == "turn_end":
            joined = "".join(text_chunks)
            print(f"  [turn_end] {len(joined)} chars, {len(cites)} cites", flush=True)
            print(f"  ---\n  {joined[:400]}{'...' if len(joined) > 400 else ''}", flush=True)
            return {"agent": agent, "model": model, "text": joined, "cites": cites, "ok": True}
        elif et == "error":
            print(f"  [error] {evt}", flush=True)
            return {"agent": agent, "text": "".join(text_chunks), "cites": cites, "ok": False}


async def main():
    sess = post_json(
        "/api/v1/prep-session",
        {"role": "CFO", "agenda_id": "sea-expansion", "agenda_topic": "SEA expansion budget"},
    )
    sid = sess["prep_session_id"]
    print(f"sid={sid}", flush=True)

    async with websockets.connect(f"{WS}/ws/prep/{sid}", ping_interval=None) as ws:
        first = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
        assert first.get("type") == "prep_ready", first
        print(f"prep_ready: role={first.get('role')} topic={first.get('agenda_topic')}", flush=True)

        post_json(
            f"/api/v1/prep-session/{sid}/message",
            {"text": "Help me defend the budget", "mode": "coach"},
        )
        coach = await collect_turn(ws, "COACH (CFO)")

        post_json(
            f"/api/v1/prep-session/{sid}/message",
            {"text": "Now drill me on the runway risk", "mode": "drill"},
        )
        drill = await collect_turn(ws, "DRILL (CFO)")

        post_json(
            f"/api/v1/prep-session/{sid}/message",
            {
                "text": "What would Legal push back with on data residency?",
                "mode": "simulate",
                "simulate_role": "Legal",
            },
        )
        sim = await collect_turn(ws, "SIMULATE (Legal)")

    fails = []
    if not coach["ok"] or len(coach["text"]) < 50:
        fails.append("coach: short or failed")
    if coach.get("agent") != "CFO":
        fails.append(f"coach: agent != CFO ({coach.get('agent')})")
    if not drill["ok"] or len(drill["text"]) < 50:
        fails.append("drill: short or failed")
    if drill.get("agent") != "CFO":
        fails.append(f"drill: agent != CFO ({drill.get('agent')})")
    if not sim["ok"] or len(sim["text"]) < 50:
        fails.append("simulate: short or failed")
    if sim.get("agent") != "Legal":
        fails.append(f"simulate: agent != Legal ({sim.get('agent')})")

    print("\n=========")
    if fails:
        print("FAIL:")
        for f in fails:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS: coach + drill + simulate all streamed end-to-end on LIVE")


asyncio.run(main())
