"""Load FaithConflict and normalize it to one row per document.

    python -m src.data --inspect     # show raw columns, categories, sample rows
    python -m src.data --prepare     # write data/faithconflict.jsonl

Normalized row:
    pair_id, doc_uid, doc_id (opaque id shown to the model), category, group,
    polarity ('confirming' | 'opposing'), claim, document, question, twin_doc_id
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import Counter

import pandas as pd

from .config import load_config, resolve, write_jsonl, read_jsonl

GROUPS = ("safety", "capability", "subjective")

CANDIDATES = {
    "pair_id": ["pair_id", "pair", "pairid", "pair_idx", "pair_index", "id", "uid", "example_id", "item_id"],
    "category": ["category", "subcategory", "sub_category", "domain", "cat", "topic_category", "task"],
    "group": ["group", "category_group", "super_category", "supercategory", "macro_category", "axis", "dimension"],
    "polarity": ["polarity", "version", "doc_type", "document_type", "stance", "side", "variant", "condition", "label", "type"],
    "claim": ["claim", "statement", "assertion", "claim_text"],
    "document": ["document", "doc", "document_text", "text", "passage", "source", "context", "content"],
    "question": ["question", "query", "qa_question"],
    "confirming_document": ["confirming_document", "confirming_doc", "doc_confirming", "document_confirming",
                            "aligned_document", "confirm_document", "confirming"],
    "opposing_document": ["opposing_document", "opposing_doc", "doc_opposing", "document_opposing",
                          "conflicting_document", "oppose_document", "opposing"],
    "confirming_claim": ["confirming_claim", "claim_confirming", "aligned_claim", "confirm_claim"],
    "opposing_claim": ["opposing_claim", "claim_opposing", "conflicting_claim", "oppose_claim"],
}

CONFIRM_WORDS = ("confirm", "align", "agree", "support", "consistent", "safe", "true", "correct", "pro")
OPPOSE_WORDS = ("oppos", "conflict", "counter", "contra", "unsafe", "false", "incorrect", "misinfo", "anti")

GROUP_KEYWORDS = [  # order matters: first match wins
    ("subjective", ("frontier", "historical", "moral", "political", "ideolog", "subjective", "control")),
    ("safety", ("misinformation", "bias", "health", "safety", "harm", "toxic")),
    ("capability", ("counterfactual", "math", "factual", "capability", "reasoning", "knowledge")),
]


# ----------------------------------------------------------------------------- loading
def load_raw(cfg: dict) -> pd.DataFrame:
    d = cfg["data"]
    if d.get("local_path"):
        p = resolve(d["local_path"])
        ext = p.suffix.lower()
        if ext == ".csv":
            return pd.read_csv(p)
        if ext in (".jsonl", ".ndjson"):
            return pd.read_json(p, lines=True)
        if ext == ".json":
            return pd.read_json(p)
        if ext == ".parquet":
            return pd.read_parquet(p)
        sys.exit(f"Unsupported local file type: {ext}")

    from datasets import load_dataset

    ds = load_dataset(d["hf_dataset"], d.get("hf_config"))
    if d.get("hf_split"):
        return ds[d["hf_split"]].to_pandas()
    frames = []
    for split, part in ds.items():
        df = part.to_pandas()
        df["_split"] = split
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _find(df: pd.DataFrame, key: str, override: str | None) -> str | None:
    if override:
        if override not in df.columns:
            sys.exit(f"config data.columns.{key} = '{override}' is not a column. Columns: {list(df.columns)}")
        return override
    lower = {c.lower(): c for c in df.columns}
    for cand in CANDIDATES[key]:
        if cand in lower:
            return lower[cand]
    return None


def _polarity(value) -> str | None:
    v = str(value).strip().lower()
    if v in ("1", "0"):
        return None  # ambiguous; must be configured
    if any(w in v for w in OPPOSE_WORDS):
        return "opposing"
    if any(w in v for w in CONFIRM_WORDS):
        return "confirming"
    return None


def _group_for(category: str, mapping: dict) -> str | None:
    if category in mapping:
        return mapping[category]
    c = str(category).lower()
    for group, words in GROUP_KEYWORDS:
        if any(w in c for w in words):
            return group
    return None


# ----------------------------------------------------------------------------- normalizing
def expand_templates(df: pd.DataFrame) -> pd.DataFrame:
    """FaithConflict on Hugging Face stores one row per pair: claim_true, claim_false and a
    summary_template with [CLAIM] placeholders. Build the two documents of each pair
    (identical except for the claim): confirming = claim_true, opposing = claim_false."""
    needed = {"summary_template", "claim_true", "claim_false"}
    if not needed <= set(df.columns) or "confirming_document" in df.columns:
        return df
    df = df.copy()
    for pol, src in (("confirming", "claim_true"), ("opposing", "claim_false")):
        claims = df[src].astype(str).str.strip().str.rstrip(".")
        df[f"{pol}_claim"] = claims
        df[f"{pol}_document"] = [str(t).replace("[CLAIM]", c) for t, c in zip(df["summary_template"], claims)]
    return df


def normalize(df: pd.DataFrame, cfg: dict) -> list[dict]:
    d = cfg["data"]
    over = d.get("columns") or {}
    df = expand_templates(df)
    col = {k: _find(df, k, over.get(k)) for k in CANDIDATES}
    wide = bool(col["confirming_document"] and col["opposing_document"]) and not (
        over.get("polarity") or over.get("document"))

    if not col["category"] and not col["group"]:
        sys.exit("Could not find a category or group column. Set data.columns.category in config.yaml.")

    rows: list[dict] = []
    if wide:
        if not col["pair_id"]:
            df = df.reset_index().rename(columns={"index": "_pair"})
            col["pair_id"] = "_pair"
        for _, r in df.iterrows():
            for pol in ("confirming", "opposing"):
                claim_col = col[f"{pol}_claim"] or col["claim"]
                rows.append({
                    "pair_id": str(r[col["pair_id"]]),
                    "category": str(r[col["category"]]) if col["category"] else None,
                    "group_raw": str(r[col["group"]]) if col["group"] else None,
                    "polarity": pol,
                    "claim": str(r[claim_col]) if claim_col else None,
                    "document": str(r[col[f"{pol}_document"]]),
                    "question": str(r[col["question"]]) if col["question"] else None,
                })
    else:
        missing = [k for k in ("pair_id", "polarity", "document") if not col[k]]
        if missing:
            sys.exit(f"Could not detect columns {missing}. Run --inspect and set them in config.yaml (data.columns).")
        bad = set()
        for _, r in df.iterrows():
            pol = _polarity(r[col["polarity"]])
            if pol is None:
                bad.add(str(r[col["polarity"]]))
                continue
            rows.append({
                "pair_id": str(r[col["pair_id"]]),
                "category": str(r[col["category"]]) if col["category"] else None,
                "group_raw": str(r[col["group"]]) if col["group"] else None,
                "polarity": pol,
                "claim": str(r[col["claim"]]) if col["claim"] else None,
                "document": str(r[col["document"]]),
                "question": str(r[col["question"]]) if col["question"] else None,
            })
        if bad:
            sys.exit(f"Could not tell confirming from opposing for polarity values {sorted(bad)}. "
                     f"Map them by editing _polarity() in src/data.py or point data.columns.polarity elsewhere.")

    # groups
    mapping = d.get("category_groups") or {}
    unmapped = set()
    for r in rows:
        g = None
        if r["group_raw"]:
            g = _group_for(r["group_raw"], mapping) or (r["group_raw"].lower() if r["group_raw"].lower() in GROUPS else None)
        if g is None and r["category"]:
            g = _group_for(r["category"], mapping)
        if g not in GROUPS:
            unmapped.add(r["category"] or r["group_raw"])
        r["group"] = g
        if r["category"] is None:
            r["category"] = r["group_raw"]
    if unmapped:
        sys.exit("These categories could not be mapped to safety/capability/subjective: "
                 f"{sorted(map(str, unmapped))}\nAdd them to data.category_groups in config.yaml.")

    # questions and claims
    for r in rows:
        if not r["claim"]:
            sys.exit("No claim column found. Set data.columns.claim (or confirming_claim/opposing_claim) in config.yaml.")
        if not r["question"]:
            claim = r["claim"].strip().rstrip(".")
            r["question"] = d["question_template"].format(claim=claim)

    # pair integrity
    by_pair: dict[str, list[dict]] = {}
    for r in rows:
        by_pair.setdefault(r["pair_id"], []).append(r)
    clean = []
    dropped = 0
    for pid, docs in by_pair.items():
        pols = sorted(x["polarity"] for x in docs)
        if pols != ["confirming", "opposing"]:
            dropped += 1
            continue
        clean.extend(docs)
    if dropped:
        print(f"WARNING: dropped {dropped} pairs that did not have exactly one confirming and one opposing document.")

    # opaque document ids (no polarity leak), deterministic shuffle
    rng = random.Random(cfg["run"].get("seed", 13))
    order = list(range(len(clean)))
    rng.shuffle(order)
    for new_idx, i in enumerate(order):
        clean[i]["doc_id"] = f"doc_{new_idx:04d}"
    for r in clean:
        r["doc_uid"] = f"{r['pair_id']}::{r['polarity']}"
        r.pop("group_raw", None)
    twin = {}
    for pid, docs in by_pair.items():
        if len(docs) == 2 and all("doc_id" in x for x in docs):
            twin[docs[0]["doc_id"]] = docs[1]["doc_id"]
            twin[docs[1]["doc_id"]] = docs[0]["doc_id"]
    for r in clean:
        r["twin_doc_id"] = twin[r["doc_id"]]
    clean.sort(key=lambda x: (x["group"], x["category"], x["pair_id"], x["polarity"]))
    return clean


def load_normalized(cfg: dict) -> list[dict]:
    rows = read_jsonl(resolve(cfg["data"]["normalized_path"]))
    if not rows:
        sys.exit("No prepared data. Run: python -m src.data --prepare")
    return rows


def balanced_pair_sample(rows: list[dict], n_pairs: int, seed: int = 13) -> set[str]:
    """Pick n_pairs pair_ids spread evenly over the three groups."""
    rng = random.Random(seed)
    by_group: dict[str, list[str]] = {}
    for r in rows:
        by_group.setdefault(r["group"], [])
        if r["pair_id"] not in by_group[r["group"]]:
            by_group[r["group"]].append(r["pair_id"])
    chosen: set[str] = set()
    per = max(1, n_pairs // max(1, len(by_group)))
    for g, ids in sorted(by_group.items()):
        ids = sorted(ids)
        rng.shuffle(ids)
        chosen.update(ids[:per])
    return chosen


# ----------------------------------------------------------------------------- CLI
def inspect(cfg: dict) -> None:
    df = load_raw(cfg)
    pd.set_option("display.max_colwidth", 80)
    print(f"Rows: {len(df)}\nColumns and types:")
    for c in df.columns:
        print(f"  - {c}: {df[c].dtype}")
    print("\nLow-cardinality columns (likely category / polarity / group):")
    for c in df.columns:
        try:
            n = df[c].nunique()
        except TypeError:
            continue
        if n <= 30:
            print(f"  {c} ({n} values): {dict(Counter(df[c].astype(str)).most_common(30))}")
    print("\nFirst 2 rows:")
    for _, r in df.head(2).iterrows():
        for c in df.columns:
            print(f"  {c}: {str(r[c])[:160]!r}")
        print("  ---")
    print("\nAuto-detected columns:")
    over = cfg["data"].get("columns") or {}
    for k in CANDIDATES:
        print(f"  {k:22s} -> {_find(df, k, over.get(k))}")


def prepare(cfg: dict) -> None:
    df = load_raw(cfg)
    rows = normalize(df, cfg)
    out = resolve(cfg["data"]["normalized_path"])
    write_jsonl(out, rows)
    pairs = Counter(r["group"] for r in rows if r["polarity"] == "opposing")
    cats = Counter((r["group"], r["category"]) for r in rows if r["polarity"] == "opposing")
    print(f"Wrote {len(rows)} documents ({len(rows) // 2} pairs) to {out}")
    print("Pairs per group:", dict(pairs), "(paper: safety 386, capability 248, subjective 306)")
    for (g, c), n in sorted(cats.items()):
        print(f"  {g:11s} {c}: {n}")
    ex = next(r for r in rows if r["polarity"] == "opposing")
    print("\nExample opposing question:\n ", ex["question"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--config")
    a = ap.parse_args()
    cfg = load_config(a.config)
    if a.inspect:
        inspect(cfg)
    if a.prepare:
        prepare(cfg)
    if not (a.inspect or a.prepare):
        ap.print_help()


if __name__ == "__main__":
    main()
