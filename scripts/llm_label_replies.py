"""Label outbound email replies with an OpenRouter model.

Usage: python scripts/llm_label_replies.py <reply_export.csv> <output.csv>

Reads OPEN_ROUTER_API_KEY from the environment or Notion/.env.
Writes one row per reply: reply_id, account_id, label, confidence, rationale.
Progress is cached next to the output, so a rerun resumes where it stopped.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
BATCH = 40
LABELS = {"ready_to_buy", "evaluating", "not_now", "not_interested", "wrong_contact"}
ROOT = Path(__file__).resolve().parent.parent
PROMPT = (ROOT / "prompts" / "label_replies.md").read_text()


def api_key() -> str:
    if os.environ.get("OPEN_ROUTER_API_KEY"):
        return os.environ["OPEN_ROUTER_API_KEY"]
    for line in (ROOT / "Notion" / ".env").read_text().splitlines():
        if line.startswith("OPEN_ROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit("OPEN_ROUTER_API_KEY not found")


def call(batch: list[dict], key: str) -> list[dict]:
    body = json.dumps({
        "model": MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": json.dumps(batch, ensure_ascii=False)},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        text = json.load(r)["choices"][0]["message"]["content"]
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    match = re.search(r"\[.*\]", text, flags=re.S)
    if not match:
        raise ValueError(f"no JSON array in response: {text[:200]}")
    return json.loads(match.group(0))


def main(src: str, out: str) -> None:
    df = pd.read_csv(src)
    cache_path = Path(out).with_suffix(".cache.json")
    done = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    key = api_key()
    todo = df[~df.reply_id.isin(done)]
    rows = todo[["reply_id", "reply_body"]].to_dict("records")
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        for attempt in range(6):
            try:
                result = call(batch, key)
                ids = {b["reply_id"] for b in batch}
                good = [r for r in result if r.get("reply_id") in ids and r.get("label") in LABELS]
                for r in good:
                    done[r["reply_id"]] = r
                cache_path.write_text(json.dumps(done))
                print(f"batch {i // BATCH + 1}: {len(good)}/{len(batch)} labelled, total {len(done)}/{len(df)}", flush=True)
                break
            except (urllib.error.HTTPError, urllib.error.URLError, ValueError, json.JSONDecodeError, KeyError, TimeoutError) as e:
                wait = 15 * (attempt + 1)
                detail = e.read().decode()[:200] if isinstance(e, urllib.error.HTTPError) else str(e)[:200]
                print(f"batch {i // BATCH + 1} attempt {attempt + 1} failed ({detail}); retry in {wait}s", flush=True)
                time.sleep(wait)
    # The model only sees reply_id and reply_body. account_id comes from the
    # source CSV, matched on reply_id.
    labelled = pd.DataFrame(done.values())[["reply_id", "label", "confidence", "rationale"]]
    final = df[["reply_id", "account_id"]].merge(labelled, on="reply_id", how="left")
    final.to_csv(out, index=False)
    missing = final.label.isna().sum()
    print(f"wrote {len(final)} rows to {out}; {missing} unlabelled (rerun to fill them)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
