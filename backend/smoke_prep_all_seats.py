"""Comprehensive live prep smoke: every seat (CEO/CFO/CMO/CTO/Legal) x every
mode (coach/drill) against the deployed backend. Mirrors the browser flow:
open WS without awaiting, POST /message, collect full turn."""
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


async def collect_turn(ws, label: str, expect_agent: str) -> dict:
    text_chunks: list[str] = []
    cites: list[dict] = []
    agent: str | None = None
    model: str | None = None
    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=180)
        except asyncio.TimeoutError:
            return {"label": label, "ok": False, "reason": "timeout", "text": "".join(text_chunks)}
        evt = json.loads(raw)
        et = evt.get("type")
        if et == "turn_start":
            agent = evt["agent"]
            model = evt["model"]
        elif et == "citation":
            cites.append(evt)
        elif et == "token":
            text_chunks.append(evt.get("text", ""))
        elif et == "turn_end":
            joined = "".join(text_chunks)
            ok = len(joined) >= 100 and agent == expect_agent
            return {
                "label": label,
                "ok": ok,
                "agent": agent,
                "expected": expect_agent,
                "model": model,
                "chars": len(joined),
                "cites": len(cites),
                "preview": joined[:120].replace("\n", " "),
            }
        elif et == "error":
            return {"label": label, "ok": False, "reason": "error_event", "evt": evt}


PROMPTS = {
    "coach":    "Help me defend the SEA expansion plan to the board.",
    "drill":    "Drill me with the toughest pushback I should expect on the SEA expansion plan.",
}

# (seat, agenda_id, agenda_topic) — pick a real agenda each time
AGENDAS = {
    "CEO":   ("sea-expansion", "Q1 2026 expansion: SEA vs double-down India"),
    "CFO":   ("sea-expansion", "SEA expansion budget approval"),
    "CMO":   ("sea-expansion", "SEA go-to-market positioning"),
    "CTO":   ("sea-expansion", "SEA infra + data residency build-out"),
    "Legal": ("sea-expansion", "SEA data-residency + customer contracts"),
}


async def run_seat(seat: str) -> list[dict]:
    aid, topic = AGENDAS[seat]
    code, sess = post_json(
        "/api/v1/prep-session",
        {"role": seat, "agenda_id": aid, "agenda_topic": topic},
    )
    if code != 200:
        return [{"label": f"{seat}/session", "ok": False, "reason": f"http {code}", "evt": sess}]
    sid = sess["prep_session_id"]

    results = []
    async with websockets.connect(
        f"{WS}/ws/prep/{sid}", ping_interval=None, origin=ORIGIN, max_size=8 * 1024 * 1024
    ) as ws:
        first = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
        if first.get("type") != "prep_ready":
            return [{"label": f"{seat}/prep_ready", "ok": False, "reason": "no_ready", "evt": first}]

        for mode in ("coach", "drill"):
            body = {"text": PROMPTS[mode], "mode": mode}
            expect = seat
            code, _ = post_json(f"/api/v1/prep-session/{sid}/message", body)
            if code != 200:
                results.append({"label": f"{seat}/{mode}", "ok": False, "reason": f"post {code}"})
                continue
            # Drain user_message echo until we hit turn_start path inside collect_turn
            res = await collect_turn(ws, f"{seat}/{mode}", expect)
            results.append(res)
    return results


async def main():
    all_results: list[dict] = []
    for seat in ("CEO", "CFO", "CMO", "CTO", "Legal"):
        print(f"\n=== {seat} ===", flush=True)
        rows = await run_seat(seat)
        for r in rows:
            ok = r.get("ok")
            tag = "PASS" if ok else "FAIL"
            extra = ""
            if ok:
                extra = f"agent={r.get('agent')} model={r.get('model')} {r.get('chars')}c {r.get('cites')}cites :: {r.get('preview')}"
            else:
                extra = json.dumps({k: v for k, v in r.items() if k not in ("label", "ok")}, default=str)[:300]
            print(f"  [{tag}] {r['label']:20s} {extra}", flush=True)
        all_results.extend(rows)

    fails = [r for r in all_results if not r.get("ok")]
    print("\n=========")
    if fails:
        print(f"FAIL: {len(fails)} of {len(all_results)} checks failed")
        for f in fails:
            print(f"  - {f['label']}: {f.get('reason') or json.dumps({k: v for k, v in f.items() if k not in ('label', 'ok')}, default=str)[:200]}")
        sys.exit(1)
    print(f"PASS: all {len(all_results)} checks (5 seats x 2 modes) streamed end-to-end on LIVE")


asyncio.run(main())
