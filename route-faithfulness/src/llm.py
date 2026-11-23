"""Thin async wrapper over any OpenAI-compatible chat API (OpenAI, OpenRouter, Together, vLLM).

Returns a plain dict so the rest of the code never touches SDK objects:
    {content, tool_calls: [{id, name, arguments}], assistant_message, reasoning_present, usage, finish_reason}
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import re

THINK_RE = re.compile(r"<think>.*?</think>", re.S)


class LLM:
    def __init__(self, model_cfg: dict, mock: bool = False, mock_role: str = "model"):
        self.cfg = model_cfg
        self.model = model_cfg["model"]
        self.extra_body = model_cfg.get("extra_body") or None
        self.mock = mock
        if mock:
            from .mock import MockClient

            self.client = MockClient(role=mock_role)
        else:
            from openai import AsyncOpenAI

            key_env = model_cfg.get("api_key_env", "OPENAI_API_KEY")
            key = os.environ.get(key_env)
            if not key:
                raise SystemExit(f"Missing API key: set {key_env} in .env")
            self.client = AsyncOpenAI(api_key=key, base_url=model_cfg.get("base_url") or None, timeout=120)

    async def chat(self, messages, tools=None, tool_choice=None, temperature=0.0, max_tokens=400,
                   response_format=None) -> dict:
        kwargs = dict(model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens)
        if tools:
            kwargs["tools"] = tools
            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice
        if response_format:
            kwargs["response_format"] = response_format
        if self.extra_body:
            kwargs["extra_body"] = self.extra_body

        delay = 2.0
        last_err = None
        for attempt in range(7):
            try:
                resp = await self.client.chat.completions.create(**kwargs)
                return _normalize(resp)
            except Exception as e:  # noqa: BLE001 - retry anything transient, surface the rest
                last_err = e
                name = type(e).__name__
                status = getattr(e, "status_code", None)
                transient = name in ("RateLimitError", "APITimeoutError", "APIConnectionError",
                                     "InternalServerError") or (status is not None and status >= 500) \
                    or status == 429
                if not transient or attempt == 6:
                    raise
                await asyncio.sleep(delay + random.random())
                delay = min(delay * 2, 60)
        raise last_err  # pragma: no cover


def _normalize(resp) -> dict:
    choice = resp.choices[0]
    msg = choice.message
    content = msg.content or ""
    reasoning = bool(getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None)
                     or "<think>" in content)
    content = THINK_RE.sub("", content).strip()
    calls = []
    for tc in (getattr(msg, "tool_calls", None) or []):
        raw = tc.function.arguments or "{}"
        try:
            args = json.loads(raw)
        except json.JSONDecodeError:
            args = {"_raw": raw}
        calls.append({"id": tc.id, "name": tc.function.name, "arguments": args, "raw_arguments": raw})
    assistant_message = {"role": "assistant", "content": content or None}
    if calls:
        assistant_message["tool_calls"] = [
            {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["raw_arguments"]}}
            for c in calls]
    usage = getattr(resp, "usage", None)
    return {
        "content": content,
        "tool_calls": calls,
        "assistant_message": assistant_message,
        "reasoning_present": reasoning,
        "finish_reason": getattr(choice, "finish_reason", None),
        "usage": {"prompt_tokens": getattr(usage, "prompt_tokens", None),
                  "completion_tokens": getattr(usage, "completion_tokens", None)} if usage else None,
    }
