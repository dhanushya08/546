"""One function per condition. Each returns the logged record for one document.

C1 Direct            document in the prompt (paper layout)                         plan: D0
C2 Direct-reshaped   same user text as C3, document inline         (wording control)  plan: D1
T1 Tool-injected     harness writes the read_document call itself  (channel only)     plan: T1
C3 Tool              model calls read_document, verbatim return    (agency)           plan: T2
C4 RAG-oracle        gold document presented as a retrieved result (presentation, no retrieval error)
C5 RAG-BM25          real top-k BM25 retrieval, twin excluded      (retrieval errors)
C6 Agent (stretch)   search_corpus + read_document, step budget    (autonomy)
"""
from __future__ import annotations

import json

from . import prompts as P

# Ladder order: tables and figures follow it.
ALL_CONDITIONS = ["C1", "C2", "T1", "C3", "C4", "C5", "C6"]
CONDITION_NAMES = {
    "C1": "Direct", "C2": "Direct-reshaped", "T1": "Tool-injected", "C3": "Tool", "C4": "RAG-oracle",
    "C5": "RAG-BM25", "C6": "Agent",
}


def order_conditions(conds) -> list[str]:
    conds = set(conds)
    return [c for c in ALL_CONDITIONS if c in conds] + sorted(conds - set(ALL_CONDITIONS))


class Context:
    def __init__(self, cfg: dict, llm, rows: list[dict], retriever):
        self.cfg = cfg
        self.run = cfg["run"]
        self.instr = cfg["prompt"]["instruction"]
        self.read_tool = P.read_tool(cfg["prompt"]["tool_description"])
        self.llm = llm
        self.injected_call_extra = (getattr(llm, "cfg", None) or {}).get("injected_tool_call_extra")
        self.by_id = {r["doc_id"]: r for r in rows}
        self.retriever = retriever

    async def ask(self, messages, tools=None, tool_choice=None):
        return await self.llm.chat(messages, tools=tools, tool_choice=tool_choice,
                                   temperature=self.run["temperature"], max_tokens=self.run["max_tokens"])

    def read_document(self, args: dict) -> str:
        did = str(args.get("doc_id", "")).strip()
        if did in self.by_id:
            return self.by_id[did]["document"]
        return f"Error: no document with ID '{did}'."


def _base(rec: dict, cond: str) -> dict:
    return {k: rec[k] for k in ("pair_id", "doc_uid", "doc_id", "category", "group", "polarity", "claim", "question")} \
        | {"condition": cond}


async def run_condition(cond: str, rec: dict, ctx: Context) -> dict:
    out = _base(rec, cond)
    fn = {"C1": _c1, "C2": _c2, "T1": _t1, "C3": _c3, "C4": _c4, "C5": _c5, "C6": _c6}[cond]
    try:
        out |= await fn(rec, ctx)
        out["error"] = None
    except Exception as e:  # noqa: BLE001 - log and continue; analysis drops errored rows
        out |= {"answer": None, "error": f"{type(e).__name__}: {str(e)[:300]}"}
    return out


async def _single_turn(messages, ctx, extra=None) -> dict:
    r = await ctx.ask(messages)
    return {"answer": r["content"], "messages": messages + [r["assistant_message"]],
            "reasoning_present": r["reasoning_present"], "finish_reason": r["finish_reason"],
            "usage": [r["usage"]], "gold_in_context": True, "tool_calls": []} | (extra or {})


async def _c1(rec, ctx):
    return await _single_turn(P.c1_direct(rec["document"], rec["question"], ctx.instr), ctx)


async def _c2(rec, ctx):
    return await _single_turn(P.c2_reshaped(rec["document"], rec["doc_id"], rec["question"], ctx.instr), ctx)


async def _c4(rec, ctx):
    msgs = P.c4_c5_rag([(rec["doc_id"], rec["document"])], rec["question"], ctx.instr)
    return await _single_turn(msgs, ctx, {"retrieved": [rec["doc_id"]], "gold_rank": 1})


async def _c5(rec, ctx):
    k = ctx.run["rag_top_k"]
    hits = ctx.retriever.search(rec["question"], exclude={rec["twin_doc_id"]}, k=k)
    ids = [h[0] for h in hits]
    gold_rank = ids.index(rec["doc_id"]) + 1 if rec["doc_id"] in ids else None
    msgs = P.c4_c5_rag([(d, ctx.by_id[d]["document"]) for d in ids], rec["question"], ctx.instr)
    res = await _single_turn(msgs, ctx, {"retrieved": ids, "retrieval_scores": [h[1] for h in hits],
                                         "gold_rank": gold_rank})
    res["gold_in_context"] = gold_rank is not None
    return res


async def _tool_loop(messages, tools, ctx, rec, max_turns, first_choice=None):
    """Generic tool loop. Returns transcript, calls, final answer and bookkeeping."""
    calls_log, usage, reasoning = [], [], False
    answer, budget_hit, finish = None, False, None
    for turn in range(max_turns + 1):
        last = turn == max_turns
        if last:
            choice = "none"  # budget spent: the model must answer now
        else:
            choice = first_choice if (turn == 0 and first_choice) else None
        r = await ctx.ask(messages, tools=tools, tool_choice=choice)
        usage.append(r["usage"])
        reasoning |= r["reasoning_present"]
        finish = r["finish_reason"]
        if r["tool_calls"] and not last:
            messages = messages + [r["assistant_message"]]
            for tc in r["tool_calls"]:
                if tc["name"] == "read_document":
                    result = ctx.read_document(tc["arguments"])
                    returned = str(tc["arguments"].get("doc_id", "")).strip()
                elif tc["name"] == "search_corpus":
                    q = str(tc["arguments"].get("query", ""))
                    hits = ctx.retriever.search(q, exclude={rec["twin_doc_id"]}, k=ctx.run["agent_search_k"])
                    result = json.dumps([{"doc_id": d, "snippet": ctx.retriever.snippet(d, q)} for d, _ in hits])
                    returned = [d for d, _ in hits]
                else:
                    result, returned = f"Error: unknown tool '{tc['name']}'.", None
                calls_log.append({"name": tc["name"], "arguments": tc["arguments"], "returned": returned})
                messages = messages + [{"role": "tool", "tool_call_id": tc["id"], "content": result}]
            continue
        answer = r["content"]
        messages = messages + [r["assistant_message"]]
        if last and r["tool_calls"]:
            budget_hit = True
        break
    return {"answer": answer, "messages": messages, "tool_calls": calls_log, "usage": usage,
            "reasoning_present": reasoning, "finish_reason": finish,
            "budget_hit": budget_hit or (answer in (None, ""))}


async def _c3(rec, ctx):
    msgs = P.c3_tool_user(rec["doc_id"], rec["question"], ctx.instr)
    force = {"type": "function", "function": {"name": "read_document"}} if ctx.run.get("force_tool_call") else None
    res = await _tool_loop(msgs, [ctx.read_tool], ctx, rec, ctx.run["max_tool_turns"], first_choice=force)
    reads = [c for c in res["tool_calls"] if c["name"] == "read_document"]
    res["gold_in_context"] = any(c["returned"] == rec["doc_id"] for c in reads)
    return res


async def _t1(rec, ctx):
    """T1: C3's user turn, then a read_document call the harness made, then the model answers.
    From here on it is C3's loop with the same budget: C3 spends its first tool round on the gold
    read, so T1 gets max_tool_turns - 1 further rounds before it must answer."""
    msgs = P.c3_tool_user(rec["doc_id"], rec["question"], ctx.instr) \
        + P.t1_injected_read(rec["doc_id"], rec["document"], ctx.injected_call_extra)
    res = await _tool_loop(msgs, [ctx.read_tool], ctx, rec, max(1, ctx.run["max_tool_turns"] - 1))
    res["tool_calls"] = [{"name": "read_document", "arguments": {"doc_id": rec["doc_id"]},
                          "returned": rec["doc_id"], "injected": True}] + res["tool_calls"]
    res["gold_in_context"] = True
    res["model_tool_calls"] = len(res["tool_calls"]) - 1  # extra calls the model chose to make
    return res


async def _c6(rec, ctx):
    msgs = P.c6_agent_user(rec["claim"], rec["question"], ctx.instr)
    res = await _tool_loop(msgs, [P.SEARCH_TOOL, ctx.read_tool], ctx, rec, ctx.run["agent_max_turns"] - 1)
    surfaced = any(isinstance(c["returned"], list) and rec["doc_id"] in c["returned"]
                   for c in res["tool_calls"] if c["name"] == "search_corpus")
    read_gold = any(c["name"] == "read_document" and c["returned"] == rec["doc_id"] for c in res["tool_calls"])
    res |= {"gold_surfaced": surfaced, "gold_in_context": read_gold,
            "docs_read": [c["returned"] for c in res["tool_calls"] if c["name"] == "read_document"],
            "n_steps": len(res["tool_calls"])}
    return res
