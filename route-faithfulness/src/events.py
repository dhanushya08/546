"""Layer 2 of the taxonomy: what went wrong in the pipeline before the answer.

R0  None: the gold document reached the model intact
R1  Tool not called                         (C3, C6)
R2  Tool error: read call did not return the gold document (wrong / malformed ID)   (C3)
R3  Retrieval miss: gold document not retrieved / never surfaced by search          (C5, C6)
R4  Wrong source: gold surfaced but the agent never read it                          (C6)
R5  Budget hit: step budget ran out, or no answer                                    (C3, C6)
"""
from __future__ import annotations

EVENT_NAMES = {
    "R0": "None", "R1": "Tool not called", "R2": "Tool error", "R3": "Retrieval miss",
    "R4": "Wrong source", "R5": "Budget hit / no answer",
}


def route_event(r: dict) -> str:
    cond = r["condition"]
    if cond in ("C1", "C2", "C4"):
        return "R0" if r.get("answer") else "R5"
    if cond == "C5":
        if r.get("gold_rank") is None:
            return "R3"
        return "R0" if r.get("answer") else "R5"
    calls = r.get("tool_calls") or []
    if cond == "C3":
        if not calls:
            return "R1"
        if not r.get("gold_in_context"):
            return "R2"
        if r.get("budget_hit") or not r.get("answer"):
            return "R5"
        return "R0"
    if cond == "C6":
        if not calls:
            return "R1"
        if not r.get("gold_surfaced"):
            return "R3"
        if not r.get("gold_in_context"):
            return "R4"
        if r.get("budget_hit") or not r.get("answer"):
            return "R5"
        return "R0"
    return "R0"
