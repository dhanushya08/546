"""Run the conditions for one model. Resumable: rerun the same command after an interruption.

    python -m src.run --model gpt4o                         # all conditions in config
    python -m src.run --model gpt4o --limit-pairs 30        # balanced smoke test
    python -m src.run --model gpt4o --conditions C3 C6
    python -m src.run --model gpt4o --mock                  # no API calls
"""
from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter
from datetime import datetime, timezone

from tqdm.asyncio import tqdm

from .conditions import ALL_CONDITIONS, Context, run_condition
from .config import load_config, read_jsonl, resolve
from .data import balanced_pair_sample, load_normalized
from .llm import LLM
from .retrieval import Retriever


def raw_path(cfg, model, cond):
    return resolve(cfg["run"]["output_dir"]) / "raw" / model / f"{cond}.jsonl"


async def run_model(cfg, model_key, conditions, limit_pairs=None, groups=None, mock=False):
    if model_key not in cfg["models"]:
        raise SystemExit(f"Unknown model '{model_key}'. Options: {list(cfg['models'])}")
    rows = load_normalized(cfg)
    corpus = rows  # retrieval always searches the full corpus
    targets = rows
    if groups:
        targets = [r for r in targets if r["group"] in groups]
    if limit_pairs:
        keep = balanced_pair_sample(targets, limit_pairs, cfg["run"].get("seed", 13))
        targets = [r for r in targets if r["pair_id"] in keep]

    llm = LLM(cfg["models"][model_key], mock=mock)
    ctx = Context(cfg, llm, corpus, Retriever(corpus))
    sem = asyncio.Semaphore(cfg["run"]["concurrency"])

    for cond in conditions:
        path = raw_path(cfg, model_key, cond)
        path.parent.mkdir(parents=True, exist_ok=True)
        done = {r["doc_uid"] for r in read_jsonl(path) if r.get("error") is None}
        # drop errored rows so they are retried
        kept = [r for r in read_jsonl(path) if r.get("error") is None]
        with open(path, "w", encoding="utf-8") as f:
            for r in kept:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        todo = [r for r in targets if r["doc_uid"] not in done]
        print(f"\n[{model_key}] {cond}: {len(done)} done, {len(todo)} to run -> {path}")
        if not todo:
            continue
        lock = asyncio.Lock()

        async def one(rec):
            async with sem:
                out = await run_condition(cond, rec, ctx)
            out["model"] = model_key
            out["model_id"] = cfg["models"][model_key]["model"]
            out["timestamp"] = datetime.now(timezone.utc).isoformat()
            async with lock:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(out, ensure_ascii=False) + "\n")
            return out

        results = await tqdm.gather(*(one(r) for r in todo), desc=f"{model_key}/{cond}")
        _report(cond, results)


def _report(cond, results):
    n = len(results)
    errs = [r for r in results if r.get("error")]
    print(f"  finished {n}, errors {len(errs)}")
    if errs:
        print("  first error:", errs[0]["error"])
        print("  (rerun the same command to retry errored rows)")
    ok = [r for r in results if not r.get("error")]
    if not ok:
        return
    if any(r.get("reasoning_present") for r in ok):
        k = sum(bool(r.get("reasoning_present")) for r in ok)
        print(f"  WARNING: reasoning/thinking output detected in {k} answers. Turn thinking off in config "
              f"(extra_body) so routes are compared without reasoning.")
    if cond in ("C3", "C6"):
        called = sum(bool(r.get("tool_calls")) for r in ok)
        gold = sum(bool(r.get("gold_in_context")) for r in ok)
        print(f"  tool called: {called}/{len(ok)}   gold document read: {gold}/{len(ok)}")
    if cond == "T1":
        extra = sum(bool(r.get("model_tool_calls")) for r in ok)
        print(f"  model called the tool again after the injected read: {extra}/{len(ok)}")
    if cond == "C5":
        hit = sum(r.get("gold_rank") is not None for r in ok)
        print(f"  Recall@k: {hit}/{len(ok)}")
    empty = sum(1 for r in ok if not r.get("answer"))
    if empty:
        print(f"  WARNING: {empty} empty answers")
    print("  polarity counts:", dict(Counter(r["polarity"] for r in ok)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--conditions", nargs="+", choices=ALL_CONDITIONS)
    ap.add_argument("--limit-pairs", type=int, help="balanced sample of N pairs for a smoke test")
    ap.add_argument("--groups", nargs="+", choices=["safety", "capability", "subjective"])
    ap.add_argument("--mock", action="store_true", help="fake model, no API calls (pipeline test)")
    ap.add_argument("--concurrency", type=int, help="override run.concurrency (e.g. 32 for a local vLLM server)")
    ap.add_argument("--config")
    a = ap.parse_args()
    cfg = load_config(a.config)
    conds = a.conditions or cfg["run"]["conditions"]
    if a.concurrency:
        cfg["run"]["concurrency"] = a.concurrency
    asyncio.run(run_model(cfg, a.model, conds, a.limit_pairs, a.groups, a.mock))


if __name__ == "__main__":
    main()
