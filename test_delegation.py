#!/usr/bin/env python3
"""Delegation smoke test — confirms CEO@CTO mention produces two visible turns.

Flow:
1. POST /api/v1/prep-session  → session id
2. WS /ws/prep/{sid}           (server pushes events; client doesn't send)
3. POST /api/v1/prep-session/{sid}/message with mentions=["CTO"]
4. Collect events; expect turn_start for CTO then turn_start for CEO.
"""
import asyncio
import json
import sys
import urllib.request

import websockets

BASE = "https://app-frontier-prod-backend.azurewebsites.net"


async def main() -> int:
    # 1. Create prep session
    req = urllib.request.Request(
        f"{BASE}/api/v1/prep-session",
        data=json.dumps({"role": "CEO", "agenda_topic": "SEA expansion delegation test"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as f:
        sid = json.loads(f.read())["prep_session_id"]
    print(f"[OK] session {sid}")

    ws_url = f"{BASE.replace('https://', 'wss://')}/ws/prep/{sid}"
    async with websockets.connect(ws_url) as ws:
        # 2. Wait for prep_ready
        first = json.loads(await ws.recv())
        assert first.get("type") == "prep_ready", first
        print("[OK] WS connected, prep_ready received")

        # 3. POST the user message
        msg_req = urllib.request.Request(
            f"{BASE}/api/v1/prep-session/{sid}/message",
            data=json.dumps({
                "text": "@CTO what is our technology spending for SEA expansion?",
                "mode": "coach",
                "mentions": ["CTO"],
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(msg_req) as f:
            print(f"[OK] message queued: {json.loads(f.read())}")

        # 4. Collect events until 2 turn_ends
        delegation_events = []
        turn_starts: list[str] = []
        turn_ends = 0
        current_agent: str | None = None
        deadline = asyncio.get_event_loop().time() + 90.0
        while True:
            timeout = max(0.5, deadline - asyncio.get_event_loop().time())
            evt_str = await asyncio.wait_for(ws.recv(), timeout=timeout)
            evt = json.loads(evt_str)
            etype = evt.get("type")

            if etype in ("delegation_start", "delegation_end"):
                delegation_events.append(evt)
                print(f"  [{etype}] from={evt.get('from_role','?')} to={evt.get('to_role','?')}")
            elif etype == "turn_start":
                agent = evt.get("agent")
                turn_starts.append(agent)
                current_agent = agent
                delegated_from = evt.get("delegated_from")
                tag = f" (delegated_from={delegated_from})" if delegated_from else ""
                print(f"  [turn_start] agent={agent}{tag}")
            elif etype == "token":
                sys.stdout.write(evt.get("text", ""))
                sys.stdout.flush()
            elif etype == "turn_end":
                turn_ends += 1
                print(f"\n  [turn_end] agent={evt.get('agent')} tokens={evt.get('tokens')} duration_ms={evt.get('duration_ms')}")
                if turn_ends >= 2:
                    break
            elif etype == "user_message":
                print(f"  [user_message] text={evt.get('text')[:60]!r}")
            elif etype == "citation":
                print(f"  [citation] agent={evt.get('agent')} src={evt.get('source_uri','')}")

    print(f"\n=== Result ===")
    print(f"turn_starts: {turn_starts}")
    print(f"delegation_events: {len(delegation_events)}")
    if turn_starts == ["CTO", "CEO"]:
        print("[PASS] CTO spoke first, then CEO synthesized")
        return 0
    print(f"[FAIL] expected ['CTO', 'CEO'], got {turn_starts}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
