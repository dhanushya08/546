"""Claude backend (official Anthropic SDK), for the Claude API and Claude on Vertex AI.

The rest of the harness speaks the OpenAI chat format (messages with `tool_calls` and `role: tool`).
This module translates that format to the Anthropic Messages API on every call and translates the
reply back, so conditions.py, judge.py and the logged transcripts stay provider-neutral.

Temperature. anthropic SDK 2.x sends API version 2026-10-21 by default, which rejects `temperature`
(400 "Extra inputs are not permitted"). Every model in this study runs at temperature 0, so this
backend keeps Claude on the previous API version on purpose:
  - Claude API: header `anthropic-version: 2023-06-01`, temperature sent through `extra_body`.
  - Vertex AI:  body field `anthropic_version: vertex-2023-10-16`, temperature through `extra_body`.
Set `anthropic_version: null` in config.yaml to use the SDK default instead (temperature is then not
sent and the model samples at its default; models from Claude 4.7 on accept only the default).

Thinking stays off: Sonnet 4.6 runs without thinking when the `thinking` parameter is omitted.
"""
from __future__ import annotations

import json
import os

import anthropic

API_PINNED_VERSION = "2023-06-01"
VERTEX_PINNED_VERSION = "vertex-2023-10-16"

FINISH = {"end_turn": "stop", "stop_sequence": "stop", "tool_use": "tool_calls", "max_tokens": "length",
          "refusal": "refusal", "pause_turn": "pause_turn"}


class AnthropicChat:
    def __init__(self, cfg: dict):
        self.model = cfg["model"]
        self.extra_body = dict(cfg.get("extra_body") or {})
        vertex = cfg.get("provider") == "anthropic_vertex"
        pin = cfg.get("anthropic_version", VERTEX_PINNED_VERSION if vertex else API_PINNED_VERSION)
        self.send_temperature = pin is not None
        if vertex:
            project = cfg.get("project") or os.environ.get(cfg.get("project_env", "GOOGLE_CLOUD_PROJECT"))
            if not project:
                raise SystemExit("Claude on Vertex needs a project: set GOOGLE_CLOUD_PROJECT in .env")
            # Auth is Google Application Default Credentials (gcloud auth application-default login).
            self.client = anthropic.AsyncAnthropicVertex(project_id=project, region=cfg.get("region", "global"),
                                                         max_retries=0, timeout=120)
            if pin:
                self.extra_body["anthropic_version"] = pin
        else:
            key_env = cfg.get("api_key_env", "ANTHROPIC_API_KEY")
            key = os.environ.get(key_env)
            if not key:
                raise SystemExit(f"Missing API key: set {key_env} in .env")
            headers = {"anthropic-version": pin} if pin else None
            # Retries are handled by LLM.chat, so the SDK's own retries are off.
            self.client = anthropic.AsyncAnthropic(api_key=key, max_retries=0, timeout=120, default_headers=headers)

    async def create(self, messages, tools=None, tool_choice=None, temperature=0.0, max_tokens=400,
                     response_format=None) -> dict:
        system, msgs = to_anthropic_messages(messages)
        kwargs = dict(model=self.model, max_tokens=max_tokens, messages=msgs)
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [to_anthropic_tool(t) for t in tools]
            tc = to_anthropic_tool_choice(tool_choice)
            if tc:
                kwargs["tool_choice"] = tc
        # response_format (JSON mode) has no direct equivalent; the judge prompt already asks for JSON
        # and judge.parse_code falls back to a regex.
        body = dict(self.extra_body)
        if self.send_temperature and temperature is not None:
            body["temperature"] = temperature
        if body:
            kwargs["extra_body"] = body
        resp = await self.client.messages.create(**kwargs)
        return normalize(resp)


# ----------------------------------------------------------------------------- request translation
def to_anthropic_tool(t: dict) -> dict:
    f = t["function"] if t.get("type") == "function" else t
    return {"name": f["name"], "description": f.get("description", ""),
            "input_schema": f.get("parameters") or {"type": "object", "properties": {}}}


def to_anthropic_tool_choice(choice):
    if choice is None:
        return None  # API default: auto
    if isinstance(choice, str):
        return {"none": {"type": "none"}, "auto": {"type": "auto"}, "required": {"type": "any"}}[choice]
    if isinstance(choice, dict) and choice.get("type") == "function":
        return {"type": "tool", "name": choice["function"]["name"]}
    return choice


def _args(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        out = json.loads(raw or "{}")
        return out if isinstance(out, dict) else {"_raw": raw}
    except json.JSONDecodeError:
        return {"_raw": raw}


def to_anthropic_messages(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """OpenAI chat messages -> (system, Anthropic messages). Consecutive tool results go into one
    user message, as the Messages API expects for parallel calls."""
    system_parts, out = [], []
    for m in messages:
        role = m["role"]
        if role == "system":
            system_parts.append(m["content"])
        elif role == "user":
            out.append({"role": "user", "content": m["content"]})
        elif role == "assistant":
            blocks = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for tc in m.get("tool_calls") or []:
                blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"],
                               "input": _args(tc["function"].get("arguments"))})
            out.append({"role": "assistant", "content": blocks or ""})
        elif role == "tool":
            block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
            prev = out[-1] if out else None
            if prev and prev["role"] == "user" and isinstance(prev["content"], list) \
                    and all(b.get("type") == "tool_result" for b in prev["content"]):
                prev["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        else:
            raise ValueError(f"Unsupported message role: {role}")
    return ("\n\n".join(system_parts) or None), out


# ----------------------------------------------------------------------------- response translation
def normalize(resp) -> dict:
    """Anthropic Message -> the same dict LLM.chat returns for OpenAI-compatible providers."""
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    calls = [{"id": b.id, "name": b.name, "arguments": dict(b.input or {}),
              "raw_arguments": json.dumps(b.input or {}, ensure_ascii=False)}
             for b in resp.content if b.type == "tool_use"]
    assistant_message = {"role": "assistant", "content": text or None}
    if calls:
        assistant_message["tool_calls"] = [
            {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["raw_arguments"]}}
            for c in calls]
    u = resp.usage
    prompt = (u.input_tokens or 0) + (getattr(u, "cache_read_input_tokens", 0) or 0) \
        + (getattr(u, "cache_creation_input_tokens", 0) or 0)
    return {
        "content": text,
        "tool_calls": calls,
        "assistant_message": assistant_message,
        "reasoning_present": any(b.type in ("thinking", "redacted_thinking") for b in resp.content),
        "finish_reason": FINISH.get(resp.stop_reason, resp.stop_reason),
        "usage": {"prompt_tokens": prompt, "completion_tokens": u.output_tokens},
    }
