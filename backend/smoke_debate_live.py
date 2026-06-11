"""Live E2E debate smoke. Drives /api/v1/session + /debate + /ws/debate."""
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


async def main():
    sess = post_json("/api/v1/session", {})
    sid = sess["session_id"]
    print(f"sid={sid}", flush=True)

    async with websockets.connect(f"{WS}/ws/debate/{sid}", ping_interval=None) as ws:
        post_json(
            "/api/v1/debate",
            {"session_id": sid, "question": "Should we approve the SEA expansion budget?", "scenario_id": "sea-expansion"},
        )

        speakers: dict[str, int] = {}
        cites = 0
        decision = None
        vote = None
        end_received = False
        events_after_end = 0
        cur_agent = None
        chars = 0
        t_start = asyncio.get_event_loop().time()
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=180)
            except asyncio.TimeoutError:
                print("TIMEOUT", flush=True)
                break
            evt = json.loads(raw)
            et = evt.get("type")
            if end_received and et in ("turn_start", "token", "turn_end", "citation"):
                events_after_end += 1
            if et == "turn_start":
                cur_agent = evt["agent"]
                speakers.setdefault(cur_agent, 0)
                print(f"[turn_start] {cur_agent} {evt.get('model')}", flush=True)
            elif et == "token":
                chars += len(evt.get("text", ""))
                if cur_agent:
                    speakers[cur_agent] = speakers.get(cur_agent, 0) + len(evt.get("text", ""))
            elif et == "citation":
                cites += 1
            elif et == "turn_end":
                pass
            elif et == "mood":
                print(f"[mood] {evt.get('label')} {evt.get('value'):.2f}", flush=True)
            elif et == "debate_end":
                decision = evt.get("decision")
                vote = evt.get("vote")
                end_received = True
                print(f"[debate_end] decision={decision[:80] if decision else None}", flush=True)
                print(f"[vote] {vote}", flush=True)
                # Drain any straggler events for 5s to detect bleed.
                # Server cleanly closing the WS after debate_end is the desired behavior.
                try:
                    while True:
                        raw2 = await asyncio.wait_for(ws.recv(), timeout=5)
                        evt2 = json.loads(raw2)
                        events_after_end += 1
                        print(f"  bleed: {evt2.get('type')}", flush=True)
                except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                    pass
                break
            elif et == "error":
                print(f"[error] {evt}", flush=True)

        elapsed = asyncio.get_event_loop().time() - t_start
        print(f"\nelapsed={elapsed:.1f}s, total_chars={chars}, cites={cites}")
        print(f"speakers: {speakers}")

    fails = []
    must_speak = {"CEO", "CFO", "CMO", "CTO", "Legal"}
    spoke = set(k for k, v in speakers.items() if v > 30)
    missing = must_speak - spoke
    if missing:
        fails.append(f"silent seats: {missing}")
    if not decision:
        fails.append("no decision")
    if not vote:
        fails.append("no vote")
    if cites < 5:
        fails.append(f"too few citations: {cites}")
    if events_after_end > 0:
        fails.append(f"events leaked after debate_end: {events_after_end}")

    print("\n=========")
    if fails:
        print("FAIL:")
        for f in fails:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS: full debate streamed end-to-end on LIVE with vote+decision and clean close")


asyncio.run(main())
