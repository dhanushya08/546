"""Check the LLM judge against human labels and report Cohen's kappa.

Option A - use your pilot hand labels (fastest):
    CSV columns: answer, claim, document, human_label   (question optional)
    human_label in: Faithful, Distancing, Topicalized, Evaded, Inverted
    python -m src.validate_judge --human-csv data/pilot_labels.csv

Option B - hand-label a fresh blind sample of this project's outputs:
    python -m src.validate_judge --export-sample 150 --models gpt4o    # writes data/human_sample.csv
    # two people fill human_label with B1..B8 / O / E, without looking at the judge
    python -m src.validate_judge --human-csv data/human_sample.csv
"""
from __future__ import annotations

import argparse
import asyncio

import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

from .config import load_config, resolve
from .judge import CODES, TIER, judge_one
from .llm import LLM

PILOT_MAP = {  # pilot label -> coarse class
    "faithful": "preserved", "distancing": "preserved", "topicalized": "O", "evaded": "E", "inverted": "B8",
}


def coarse_from_code(code: str) -> str:
    if code in ("B1", "B2", "B3", "B4", "B5"):
        return "preserved"
    if code in ("B8", "O", "E"):
        return code
    return "other"


def export_sample(cfg, n, models):
    from .analyze import load

    df = load(cfg, models)
    df = df[df.valid & (df.polarity == "opposing")]
    per = max(1, n // max(1, df.condition.nunique()))
    sample = pd.concat([g.sample(min(len(g), per), random_state=0) for _, g in df.groupby("condition")])
    docs = {r["doc_uid"]: r for r in pd.read_json(resolve(cfg["data"]["normalized_path"]), lines=True)
            .to_dict("records")}
    sample = sample.sample(frac=1, random_state=1)  # shuffle so conditions are mixed (blind)
    from .judge import context_docs
    by_id = {r["doc_id"]: r for r in docs.values()}
    # labellers must see the same other documents the model (and the judge) saw
    other_docs = ["\n\n".join(f"{lab}\n{txt}" for lab, txt in context_docs(r, by_id)[1])
                  for r in sample.to_dict("records")]
    out = pd.DataFrame({
        "item": range(1, len(sample) + 1),
        "model": sample.model.values, "condition": sample.condition.values, "doc_uid": sample.doc_uid.values,
        "claim": sample.claim.values,
        "document": [docs[u]["document"] for u in sample.doc_uid],
        "other_documents": other_docs,
        "answer": sample.answer.values,
        "human_label": "",
    })
    path = resolve("data/human_sample.csv")
    out.to_csv(path, index=False)
    print(f"Wrote {len(out)} items to {path}. Hide the model/condition columns while labelling.")


async def _judge_rows(cfg, rows, mock):
    llm = LLM(cfg["judge"], mock=mock, mock_role="judge")
    sem = asyncio.Semaphore(cfg["judge"].get("concurrency", 16))

    async def one(r):
        other = r.get("other_documents")
        others = [("Other document", other)] if isinstance(other, str) and other.strip() else None
        async with sem:
            j = await judge_one(llm, r["claim"], r["document"], r.get("question", ""), r["answer"], others=others)
        return j["code"]

    return await asyncio.gather(*(one(r) for r in rows))


def validate(cfg, path, mock=False):
    h = pd.read_csv(path).dropna(subset=["human_label"])
    h = h[h.human_label.astype(str).str.strip() != ""]
    if h.empty:
        raise SystemExit("No filled human_label values.")
    if "judge_code" not in h.columns:
        # look up existing judge labels if the rows came from export_sample, else run the judge now
        if {"model", "condition", "doc_uid"} <= set(h.columns):
            from .analyze import load

            j = load(cfg)[["model", "condition", "doc_uid", "code"]].rename(columns={"code": "judge_code"})
            h = h.merge(j, on=["model", "condition", "doc_uid"], how="left")
        else:
            h["judge_code"] = asyncio.run(_judge_rows(cfg, h.to_dict("records"), mock))
    h = h.dropna(subset=["judge_code"])
    labels = h.human_label.astype(str).str.strip()

    if labels.str.upper().isin(CODES).all():
        hum = labels.str.upper()
        print(f"n = {len(h)}")
        print(f"Kappa, exact code (B1..B8, O, E):  {cohen_kappa_score(hum, h.judge_code):.3f}")
        print(f"Kappa, three tiers:                {cohen_kappa_score(hum.map(TIER), h.judge_code.map(TIER)):.3f}")
        fh = hum.isin(["B1", "B2"])
        fj = h.judge_code.isin(["B1", "B2"])
        print(f"Kappa, faithful vs not:            {cohen_kappa_score(fh, fj):.3f}  (paper's judge: 0.95)")
        print(f"Raw agreement, faithful vs not:    {(fh == fj).mean():.3f}")
    else:
        hum = labels.str.lower().map(PILOT_MAP)
        if hum.isna().any():
            raise SystemExit(f"Unknown pilot labels: {sorted(set(labels[hum.isna()]))}")
        jud = h.judge_code.map(coarse_from_code)
        print(f"n = {len(h)} (pilot labels mapped: Faithful/Distancing->preserved, Topicalized->O, "
              f"Evaded->E, Inverted->B8)")
        print(f"Kappa, coarse classes:             {cohen_kappa_score(hum, jud):.3f}")
        print(f"Kappa, inverted vs not:            {cohen_kappa_score(hum == 'B8', jud == 'B8'):.3f}")
        cls = ["preserved", "O", "E", "B8", "other"]
        cm = pd.DataFrame(confusion_matrix(hum, jud, labels=cls), index=[f"human {c}" for c in cls],
                          columns=[f"judge {c}" for c in cls])
        print(cm)
    out = resolve("results/judge_validation.csv")
    out.parent.mkdir(exist_ok=True)
    h.to_csv(out, index=False)
    print(f"Saved item-level comparison to {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human-csv")
    ap.add_argument("--export-sample", type=int)
    ap.add_argument("--models", nargs="+")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--config")
    a = ap.parse_args()
    cfg = load_config(a.config)
    if a.export_sample:
        export_sample(cfg, a.export_sample, a.models)
    if a.human_csv:
        validate(cfg, resolve(a.human_csv), a.mock)
    if not (a.export_sample or a.human_csv):
        ap.print_help()


if __name__ == "__main__":
    main()
