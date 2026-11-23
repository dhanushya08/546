"""BM25 over the whole corpus. The twin of the gold document is always excluded,
because confirming and opposing documents are near-identical and the twin would
otherwise dominate retrieval."""
from __future__ import annotations

import re

import numpy as np
from rank_bm25 import BM25Okapi

STOP = set("""a an the of to in on for and or is are was were be been by with as at from that this
these those it its into than then their there which who whom what whether about based solely
does do did study document documents states conclude""".split())
TOK = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [t for t in TOK.findall(text.lower()) if t not in STOP]


class Retriever:
    def __init__(self, rows: list[dict]):
        self.ids = [r["doc_id"] for r in rows]
        self.text = {r["doc_id"]: r["document"] for r in rows}
        self.bm25 = BM25Okapi([tokenize(r["document"]) for r in rows])

    def search(self, query: str, exclude: set[str] | None = None, k: int = 3) -> list[tuple[str, float]]:
        exclude = exclude or set()
        scores = self.bm25.get_scores(tokenize(query))
        out = []
        for i in np.argsort(-scores):
            did = self.ids[i]
            if did in exclude:
                continue
            out.append((did, float(scores[i])))
            if len(out) == k:
                break
        return out

    def snippet(self, doc_id: str, query: str, n_words: int = 40) -> str:
        """The sentence that best matches the query, so search results are informative
        even though every document starts with the same template text."""
        q = set(tokenize(query))
        sents = re.split(r"(?<=[.!?])\s+", self.text[doc_id])
        best = max(sents, key=lambda s: len(q & set(tokenize(s))))
        words = best.split()
        return " ".join(words[:n_words]) + (" ..." if len(words) > n_words else "")
