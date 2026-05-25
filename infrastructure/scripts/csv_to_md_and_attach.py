"""Convert the 7 unsupported CSV blobs into Markdown tables, upload them as
.md files to the Foundry project, attach to the boardroom-iq vector store."""

from __future__ import annotations

import csv
import os
import sys
import time
from pathlib import Path

import httpx
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = (
    "https://aif-frontier-prod-foundry.services.ai.azure.com/api/projects/proj-aif-frontier-prod"
)
VECTOR_STORE_ID = "vs_Dl4jtKh65PHtpGUU59V6WE8o"
SRC = Path(__file__).parent / ".attach_knowledge_tmp"


def csv_to_md(p: Path) -> str:
    rows = list(csv.reader(p.read_text(encoding="utf-8").splitlines()))
    if not rows:
        return ""
    header, *body = rows
    out = [f"# {p.stem.replace('__', ' / ').replace('-', ' ')}", ""]
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in body:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out) + "\n"


def main() -> int:
    cred = DefaultAzureCredential()

    def auth():
        return {"Authorization": f"Bearer {cred.get_token('https://ai.azure.com/.default').token}"}

    csvs = sorted(SRC.glob("*.csv"))
    print(f"Found {len(csvs)} CSVs")

    md_dir = SRC / "_md"
    md_dir.mkdir(exist_ok=True)

    with httpx.Client(timeout=120.0) as client:
        for c in csvs:
            md = csv_to_md(c)
            target = md_dir / (c.stem + ".md")
            target.write_text(md, encoding="utf-8")
            print(f"  converted {c.name} -> {target.name} ({len(md)} chars)", flush=True)

            fid = None
            for attempt in range(3):
                try:
                    with target.open("rb") as fh:
                        r = client.post(
                            f"{PROJECT_ENDPOINT}/openai/v1/files",
                            headers=auth(),
                            files={"file": (target.name, fh, "text/markdown")},
                            data={"purpose": "assistants"},
                        )
                    r.raise_for_status()
                    fid = r.json()["id"]
                    break
                except (httpx.HTTPError, httpx.ReadError) as e:
                    print(f"     upload attempt {attempt + 1} failed: {e}", flush=True)
                    time.sleep(2 ** attempt)
            if fid is None:
                print("     [SKIP] could not upload after retries", flush=True)
                continue
            print(f"     uploaded -> {fid}", flush=True)

            for attempt in range(3):
                try:
                    ar = client.post(
                        f"{PROJECT_ENDPOINT}/openai/v1/vector_stores/{VECTOR_STORE_ID}/files",
                        headers={**auth(), "Content-Type": "application/json"},
                        json={"file_id": fid},
                    )
                    if ar.status_code >= 400:
                        print(f"     [WARN] attach failed: {ar.status_code} {ar.text[:200]}", flush=True)
                    else:
                        print("     attached", flush=True)
                    break
                except (httpx.HTTPError, httpx.ReadError) as e:
                    print(f"     attach attempt {attempt + 1} failed: {e}", flush=True)
                    time.sleep(2 ** attempt)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
