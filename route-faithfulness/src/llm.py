"""Thin async wrapper over the chat APIs used in the study. Set `provider` per model in config.yaml:

    openai          (default) any OpenAI-compatible API: OpenAI, OpenRouter, Groq, Gemini API, vLLM
    vertex_openai   Vertex AI's OpenAI-compatible endpoint (Gemini, MaaS open models), gcloud ADC auth
    anthropic       Claude API, through the Anthropic SDK (src/llm_anthropic.py)
    anthropic_vertex Claude on Vertex AI, through the Anthropic SDK, gcloud ADC auth

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


class EmptyResponseError(Exception):
    """The API returned a choice without a message (seen occasionally on Gemini). Retried."""


class _VertexToken:
    """Google ADC access token for the Vertex OpenAI-compatible endpoint. Tokens last about an
    hour, so it is refreshed a few minutes before expiry; the OpenAI client asks for it per request."""

    def __init__(self):
        import google.auth

        self.creds, self.project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        self.lock = asyncio.Lock()
        self.refreshes = 0

    async def __call__(self) -> str:
        async with self.lock:
            # `valid` turns False a few minutes before expiry (google-auth's refresh threshold).
            if not self.creds.valid:
                import google.auth.transport.requests

                await asyncio.to_thread(self.creds.refresh, google.auth.transport.requests.Request())
                self.refreshes += 1
            return self.creds.token


def vertex_openai_base_url(project: str, location: str) -> str:
    host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
    return f"https://{host}/v1/projects/{project}/locations/{location}/endpoints/openapi"


class LLM:
    def __init__(self, model_cfg: dict, mock: bool = False, mock_role: str = "model"):
        self.cfg = model_cfg
        self.model = model_cfg["model"]
        self.extra_body = model_cfg.get("extra_body") or None
        self.mock = mock
        self.provider = model_cfg.get("provider", "openai")
        self.backend = None  # set for providers that do not use the OpenAI SDK
        if mock:
            from .mock import MockClient

            self.client = MockClient(role=mock_role)
        elif self.provider in ("anthropic", "anthropic_vertex"):
            from .llm_anthropic import AnthropicChat

            self.backend = AnthropicChat(model_cfg)
        elif self.provider == "vertex_openai":
            from openai import AsyncOpenAI

            token = _VertexToken()
            project = model_cfg.get("project") or os.environ.get(model_cfg.get("project_env", "GOOGLE_CLOUD_PROJECT")) \
                or token.project
            if not project:
                raise SystemExit("Vertex AI needs a project: set GOOGLE_CLOUD_PROJECT in .env")
            base = vertex_openai_base_url(project, model_cfg.get("location", "global"))
            self.client = AsyncOpenAI(api_key=token, base_url=base, timeout=120)
        elif self.provider == "openai":
            from openai import AsyncOpenAI

            key_env = model_cfg.get("api_key_env", "OPENAI_API_KEY")
            key = os.environ.get(key_env)
            if not key:
                raise SystemExit(f"Missing API key: set {key_env} in .env")
            self.client = AsyncOpenAI(api_key=key, base_url=model_cfg.get("base_url") or None, timeout=120)
        else:
            raise SystemExit(f"Unknown provider '{self.provider}' for model {self.model}")

    async def chat(self, messages, tools=None, tool_choice=None, temperature=0.0, max_tokens=400,
                   response_format=None) -> dict:
        if self.backend is not None:
            return await self._retry(lambda: self.backend.create(
                messages, tools=tools, tool_choice=tool_choice, temperature=temperature,
                max_tokens=max_tokens, response_format=response_format))
        kwargs = dict(model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens)
        if tools:
            kwargs["tools"] = tools
            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice
        if response_format:
            kwargs["response_format"] = response_format
        if self.extra_body:
            kwargs["extra_body"] = self.extra_body

        async def call():
            return _normalize(await self.client.chat.completions.create(**kwargs))

        return await self._retry(call)

    @staticmethod
    async def _retry(call):
        delay = 2.0
        last_err = None
        for attempt in range(7):
            try:
                return await call()
            except Exception as e:  # noqa: BLE001 - retry anything transient, surface the rest
                last_err = e
                name = type(e).__name__
                status = getattr(e, "status_code", None)
                transient = name in ("RateLimitError", "APITimeoutError", "APIConnectionError",
                                     "InternalServerError", "EmptyResponseError") \
                    or (status is not None and status >= 500) \
                    or status == 429
                if not transient or attempt == 6:
                    raise
                await asyncio.sleep(delay + random.random())
                delay = min(delay * 2, 60)
        raise last_err  # pragma: no cover


def _normalize(resp) -> dict:
    choice = resp.choices[0]
    msg = choice.message
    usage = getattr(resp, "usage", None)
    if msg is None:
        finish = getattr(choice, "finish_reason", None)
        if finish in ("malformed_response", "malformed_function_call"):
            # Gemini: the model itself produced an unparseable tool call. Repeats on retry, so it is
            # logged as the model's outcome (empty answer -> route event R5), not as an API error.
            return {"content": "", "tool_calls": [], "assistant_message": {"role": "assistant", "content": None},
                    "reasoning_present": False, "finish_reason": finish,
                    "usage": {"prompt_tokens": getattr(usage, "prompt_tokens", None),
                              "completion_tokens": getattr(usage, "completion_tokens", None)} if usage else None}
        raise EmptyResponseError(f"no message in response (finish_reason={finish})")
    content = msg.content or ""
    details = getattr(usage, "completion_tokens_details", None)
    reasoning = bool(getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None)
                     or "<think>" in content or (getattr(details, "reasoning_tokens", None) or 0) > 0)
    content = THINK_RE.sub("", content).strip()
    calls = []
    for tc in (getattr(msg, "tool_calls", None) or []):
        raw = tc.function.arguments or "{}"
        try:
            args = json.loads(raw)
        except json.JSONDecodeError:
            args = {"_raw": raw}
        # Provider-specific fields on the call, e.g. Gemini 3's extra_content.google.thought_signature.
        # They must be echoed back in the next request (Gemini 3 returns 400 without the signature).
        extra = {k: v for k, v in (getattr(tc, "model_extra", None) or {}).items() if v is not None}
        calls.append({"id": tc.id, "name": tc.function.name, "arguments": args, "raw_arguments": raw,
                      "extra": extra})
    assistant_message = {"role": "assistant", "content": content or None}
    if calls:
        assistant_message["tool_calls"] = [
            {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["raw_arguments"]}}
            | c["extra"] for c in calls]
    return {
        "content": content,
        "tool_calls": calls,
        "assistant_message": assistant_message,
        "reasoning_present": reasoning,
        "finish_reason": getattr(choice, "finish_reason", None),
        "usage": {"prompt_tokens": getattr(usage, "prompt_tokens", None),
                  "completion_tokens": getattr(usage, "completion_tokens", None)} if usage else None,
    }
