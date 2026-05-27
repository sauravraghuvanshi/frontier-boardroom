"""Live WS smoke — proves CFO (Databricks/Claude) unsticks after the
consolidate_messages + try/except fix shipped in rag-2026-05-27a."""

from __future__ import annotations

import asyncio
import json
import sys

import httpx
import websockets

BASE = "https://app-frontier-prod-backend.azurewebsites.net"
WS = "wss://app-frontier-prod-backend.azurewebsites.net"
QUESTION = "Should we open a Singapore office to anchor SEA expansion in FY27?"


async def main() -> int:
    async with httpx.AsyncClient(timeout=30.0) as http:
        r = await http.post(f"{BASE}/api/v1/session")
        r.raise_for_status()
        sid = r.json()["session_id"]
        print(f"session={sid}")

        # connect WS BEFORE /debate so we don't miss early events
        ws_url = f"{WS}/ws/debate/{sid}"
        async with websockets.connect(ws_url, max_size=2**22) as ws:
            r = await http.post(
                f"{BASE}/api/v1/debate",
                json={"session_id": sid, "question": QUESTION},
            )
            r.raise_for_status()
            print(f"debate={r.json()['debate_id']}")

            buffers: dict[str, list[str]] = {}
            turn_ends: dict[str, dict] = {}
            errors: list[str] = []
            try:
                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=120.0)
                    ev = json.loads(raw)
                    t = ev.get("type")
                    if t == "token":
                        a = ev["agent"]
                        buffers.setdefault(a, []).append(ev["text"])
                        if "provider error" in ev["text"]:
                            errors.append(f"{a}: {ev['text'][:200]}")
                    elif t == "turn_end":
                        a = ev["agent"]
                        turn_ends[a] = ev
                        text = "".join(buffers.get(a, ""))[:120].replace("\n", " ")
                        print(f"turn_end {a} tokens={ev.get('tokens')} preview={text!r}")
                    elif t == "debate_end":
                        print(f"debate_end decision={ev.get('decision','')[:120]!r}")
                        print(f"vote={ev.get('vote')}")
                        break
            except asyncio.TimeoutError:
                print("TIMEOUT waiting for events")

        # ---- assertions ----
        ok = True
        cfo = turn_ends.get("CFO")
        if not cfo:
            print("FAIL: no CFO turn_end")
            ok = False
        elif cfo.get("tokens", 0) < 5:
            print(f"FAIL: CFO produced too few tokens: {cfo.get('tokens')}")
            ok = False
        cfo_text = "".join(buffers.get("CFO", []))
        if "provider error" in cfo_text:
            print(f"FAIL: CFO provider error in stream: {cfo_text[:300]!r}")
            ok = False
        if errors:
            for e in errors:
                print(f"ERROR-token: {e}")
        if ok:
            print("PASS: CFO turn unstuck")
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
