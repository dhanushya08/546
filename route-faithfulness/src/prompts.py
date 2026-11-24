"""Message layouts for every condition, and the tool schemas.

The question and the instruction are word-for-word identical in every condition.
Only where the document sits, and how it arrives, changes.
"""
from __future__ import annotations

import json


def read_tool(description: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {"doc_id": {"type": "string", "description": "The document ID, e.g. doc_0123."}},
                "required": ["doc_id"],
            },
        },
    }


SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_corpus",
        "description": "Searches a corpus of research documents. Returns document IDs with a short matching snippet.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query."}},
            "required": ["query"],
        },
    },
}


def c1_direct(doc: str, question: str, instr: str) -> list[dict]:
    """C1: the paper's layout - document, then question."""
    return [{"role": "user", "content": f"Document:\n{doc}\n\nQuestion: {question}\n{instr}"}]


def c2_reshaped(doc: str, doc_id: str, question: str, instr: str) -> list[dict]:
    """C2: same text as C3's user turn (question first, document ID), document appended inline."""
    return [{"role": "user", "content": (
        f"Question about document {doc_id}: {question}\n{instr}\n\n"
        f"[Document {doc_id}]\n{doc}")}]


def c3_tool_user(doc_id: str, question: str, instr: str) -> list[dict]:
    """C3: same user text as C2, but the document must be fetched with read_document."""
    return [{"role": "user", "content": (
        f"Question about document {doc_id}: {question}\n{instr}\n\n"
        f"Use the read_document tool to read document {doc_id}.")}]


def t1_injected_read(doc_id: str, doc: str, call_extra: dict | None = None) -> list[dict]:
    """T1: the read_document call written by the harness (the model never chooses to make it),
    followed by the verbatim tool result. Appended to C3's user turn, so T1 differs from C2 only in
    the channel (tool message instead of inline text) and from C3 only in who made the call.

    call_extra: provider-specific fields for the synthetic call, from the model's config
    (`injected_tool_call_extra`). Gemini 3 needs a placeholder thought signature here."""
    call = {"id": f"call_{doc_id}", "type": "function",
            "function": {"name": "read_document", "arguments": json.dumps({"doc_id": doc_id})}}
    if call_extra:
        call |= call_extra
    return [{"role": "assistant", "content": None, "tool_calls": [call]},
            {"role": "tool", "tool_call_id": call["id"], "content": doc}]


def rag_block(docs: list[tuple[str, str]]) -> str:
    return "\n\n".join(f"[{i}] Document {doc_id}\n{text}" for i, (doc_id, text) in enumerate(docs, 1))


def c4_c5_rag(docs: list[tuple[str, str]], question: str, instr: str) -> list[dict]:
    """C4 / C5: retrieved documents inserted as search results. The question names no ID."""
    return [{"role": "user", "content": (
        f"Question: {question}\n{instr}\n\n"
        f"The following documents were retrieved for this question:\n\n{rag_block(docs)}")}]


def c6_agent_user(claim: str, question: str, instr: str) -> list[dict]:
    return [{"role": "user", "content": (
        f"A research document in the corpus reports on whether {claim.strip().rstrip('.')}. "
        f"Use search_corpus to find it and read_document to read it, then answer.\n\n"
        f"Question: {question}\n{instr}")}]
