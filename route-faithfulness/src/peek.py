"""Print a few transcripts so you can eyeball what the model actually saw and said.

    python -m src.peek --model gpt4o --condition C3 --n 3
    python -m src.peek --model gpt4o --condition C3 --polarity opposing --n 5
"""
from __future__ import annotations

import argparse
import json
import random

from .config import load_config, read_jsonl, resolve


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--condition", required=True)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--polarity", choices=["confirming", "opposing"])
    ap.add_argument("--full", action="store_true", help="print full message contents")
    ap.add_argument("--config")
    a = ap.parse_args()
    cfg = load_config(a.config)
    rows = read_jsonl(resolve(cfg["run"]["output_dir"]) / "raw" / a.model / f"{a.condition}.jsonl")
    if a.polarity:
        rows = [r for r in rows if r["polarity"] == a.polarity]
    random.seed(0)
    for r in random.sample(rows, min(a.n, len(rows))):
        print("=" * 100)
        print(f"{r['doc_uid']}  group={r['group']}  polarity={r['polarity']}  error={r.get('error')}")
        print(f"CLAIM: {r['claim']}")
        for m in r.get("messages", []):
            content = m.get("content") or ""
            if not a.full and len(content) > 600:
                content = content[:600] + f" ... [{len(content)} chars]"
            extra = f" tool_calls={json.dumps([t['function'] for t in m['tool_calls']])}" if m.get("tool_calls") else ""
            print(f"--- {m['role']}{extra}\n{content}")
        print(f">>> ANSWER: {r.get('answer')}")


if __name__ == "__main__":
    main()
