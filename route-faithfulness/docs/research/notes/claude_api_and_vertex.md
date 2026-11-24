# Calling Claude (Sonnet 4.6, Haiku 4.5, Haiku 5.5) via the Claude API and Google Cloud Vertex AI with the `anthropic` Python SDK (as of 2026-11-23)

Notes on sources and naming:
- Research date: 2026-11-23. All doc pages were fetched live on that date unless marked otherwise. The SDK facts come from the `anthropics/anthropic-sdk-python` GitHub repo (`main` branch and the `v1.17.0` and `v0.125.0` tags), read with curl. PyPI was checked the same day.
- **Naming change.** Anthropic's docs now call Claude on Vertex AI **"Claude Models on Google Cloud (Google managed)"**. Google's docs now say **"Agent Platform"** / "Gemini Enterprise Agent Platform" instead of "Vertex AI". Old `cloud.google.com/vertex-ai/...` URLs now 301-redirect to `docs.cloud.google.com/...`.
- **A second Google Cloud offering exists.** "Claude Models on Google Cloud (Anthropic managed)" uses the `AnthropicGoogleCloud` client and the host `claude.googleapis.com`. It is billed through Google Cloud Marketplace. It is **not** Vertex, and it is not the subject of these notes except where it helps.

---

## Q1. Is `claude-sonnet-4-6` on Vertex AI Model Garden now? Model IDs, regions, enablement, and default quotas (plus Haiku 4.5 and Haiku 5.5)

### Takeaway
Yes. Claude Sonnet 4.6 is GA on Vertex. Its model ID is `claude-sonnet-4-6`, with no `@date` suffix. It runs on the `global` endpoint and the regional endpoints `us-east5`, `europe-west1` and `asia-southeast1`. Haiku 4.5 uses the ID `claude-haiku-4-5@20251001` (global, us-east5, europe-west1). Haiku 5.5 uses `claude-haiku-5-5` and runs only on the global endpoint and the `us`/`eu` multi-region endpoints, not on single regions. You enable Claude from its Model Garden model card, which needs the Consumer Procurement Entitlement Manager role. Default global quotas: Sonnet 4.6 has 1,500 QPM, 1.5M input TPM and 150K output TPM. Haiku 4.5 has 2,500 QPM. Haiku 5.5 has 3,000 QPM.

### Cited Findings
- **Vertex model ID table:**
  - Claude Sonnet 4.6 → `claude-sonnet-4-6`
  - Claude Haiku 5.5 → `claude-haiku-5-5`
  - Claude Haiku 4.5 → `claude-haiku-4-5@20251001`
  - Sonnet 4.5 → `claude-sonnet-4-5@20250929`, marked deprecated
  - Source: [Claude Models on Google Cloud (Google managed)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)
- Rule for older IDs: "If you use a model earlier than Claude 4.6, replace the hyphen before the snapshot date in its ID with `@`." Claude 4.6 and later models use their Claude API IDs on both Google offerings — [Google managed page](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed); [Google Cloud overview](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/overview)
- Google's Sonnet 4.6 model page lists:
  - Model ID `claude-sonnet-4-6`, launch stage **GA**
  - Regions: `us-east5`, `europe-west1` and `asia-southeast1`, plus the "global endpoint"
  - Features: batch predictions, function calling, prompt caching, count tokens, extended thinking
  - Limits: 1,000,000 max input tokens and 128,000 max output tokens
  - The page gives no launch or retirement date.
  - Source: [Google Cloud – Claude Sonnet 4.6](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/partner-models/claude/sonnet-4-6)
- Endpoint types:
  - Global → region value `"global"`, host `aiplatform.googleapis.com`
  - Multi-region → `"us"` or `"eu"`, hosts `aiplatform.us.rep.googleapis.com` / `aiplatform.eu.rep.googleapis.com`
  - Regional → for example `"us-east5"`, host `{region}-aiplatform.googleapis.com`
  - "Regional endpoints serve Claude Sonnet 4.6 and earlier models only. For newer models, use a global or multi-region endpoint."
  - Source: [Google managed page](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)
- Google chooses which models each region offers and sets their lifecycle dates. These "can differ from the Claude API schedule". To check a region, search "Claude" in Model Garden — [Google managed page](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)
- **Default quotas (QPM / input TPM / output TPM)** — [Google Cloud – Quotas for Anthropic Claude models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude/quotas):
  - Sonnet 4.6:
    - us-east5: 1,500 / 1,500,000 / 150,000
    - europe-west1: 1,800 / 1,800,000 / 180,000
    - asia-southeast1: 1,500 / 1,500,000 / 150,000
    - global: 1,500 / 1,500,000 / 150,000
  - Haiku 4.5:
    - us-east5: 1,500 / 1.5M / 150K
    - europe-west1: 1,800 / 1.8M / 180K
    - global: 2,500 / 2.5M / 250K
  - Haiku 5.5 (a "shared lineage" quota):
    - `us`: 1,500 / 15M / 1.5M
    - `eu`: 1,500 / 15M / 1.5M
    - global: 3,000 / 30M / 3M
    - No regional rows.
  - You request increases on the Cloud console's **Quotas & System Limits** page. For lineage quotas, filter by `base_model`. The global endpoint and each multi-region endpoint are independent quota buckets.
- **Enabling a model:**
  - "To access a Claude on Google Cloud model, go to its Model Garden model card." — [Google Cloud – Anthropic Claude models on Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude)
  - Grant the **Consumer Procurement Entitlement Manager** role, which "lets its holder enable partner models in Model Garden".
  - Callers need the **Agent Platform User** role (`roles/aiplatform.user`, which includes `aiplatform.endpoints.predict`).
  - Org policy must allow the Cloud Commerce Consumer Procurement API (`cloudcommerceconsumerprocurement.googleapis.com`). If a policy restricts Model Garden models, "the policy must allow access to partner models".
  - Source: [Google Cloud – Use partner models](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-partner-models)
- Service to enable on the project: the Agent Platform API, `aiplatform.googleapis.com` — [Google Cloud overview (Anthropic docs)](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/overview)
- Request payloads on Agent Platform are limited to 30 MB — [Google managed page](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)

### Inferences
- For this harness, use `region="global"`. It has the same quota as us-east5 for Sonnet 4.6, a higher quota for Haiku, and costs 10% less (see Q6). It is also the only single endpoint that serves all three candidate models.
- At 1,500 QPM and 150K output TPM, a 400-token output cap allows at most about 375 maximal-length responses per minute on global. Throttle the asyncio semaphore to roughly 10–20 concurrent requests and retry 429s. About 11k calls should finish in under an hour.
- Avoid Sonnet 4.5 (`claude-sonnet-4-5@20250929`). It retires on the first-party API on 2026-11-30, according to the bundled claude-api skill model catalog. Google sets its own date.

### Gaps
- No primary source confirms whether new projects start with these quotas or with 0. The quotas page does not say.
- No retirement or shutdown date was found for Sonnet 4.6 on Vertex. Google's model page lists none.
- Not confirmed whether Sonnet 4.6 is served on the `us`/`eu` multi-region endpoints. The quotas page lists only us-east5, europe-west1, asia-southeast1 and global for it.
- The exact Model Garden UI steps (button labels, terms dialog) were not found in text form.

---

## Q2. Python SDK: `AsyncAnthropicVertex` constructor and authentication; can an express-mode API key (`AQ.…`) authenticate Claude on Vertex?

### Takeaway
Install with `pip install "anthropic[vertex]"`. Call `AsyncAnthropicVertex(project_id=..., region="global")`. Authentication uses Google Application Default Credentials (`gcloud auth application-default login`), or an explicit `access_token=` or `credentials=`. The client has **no `api_key` parameter**. Express-mode API keys are documented for a small list of Gemini models only. So plan on OAuth/ADC for Claude; an `AQ.` key will not work as far as any source shows.

### Cited Findings
- Install: `pip install -U "anthropic[vertex]"`. Example usage: `AnthropicVertex(project_id=project_id, region="global")` followed by `client.messages.create(model="claude-opus-5-5", ...)`. "The SDK … moves your `model` value into the URL and sets `anthropic_version` to the API version that it uses with the Claude API." — [Google managed page](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)
- Prerequisites:
  - The calling identity needs `aiplatform.endpoints.predict`, for example via `roles/aiplatform.user`.
  - "To authenticate the SDK with Google Cloud, you might need to run `gcloud auth application-default login`."
  - cURL uses `gcloud auth print-access-token`, which reads the gcloud CLI's own login, not ADC.
  - Source: [Google managed page](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)
- `AsyncAnthropicVertex.__init__` (main branch) — [SDK source: lib/vertex/_client.py](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/lib/vertex/_client.py):
  - Parameters: `region`, `project_id`, `access_token: str | None`, `credentials: GoogleCredentials | None`, `base_url`, `timeout`, `max_retries`, `default_headers`, `default_query`, `open_telemetry`, `http_client`, `middleware`.
  - Environment fallbacks: `CLOUD_ML_REGION` (region), `ANTHROPIC_VERTEX_PROJECT_ID` (project), `ANTHROPIC_VERTEX_BASE_URL`.
  - **No `api_key` parameter**, and no `x-goog-api-key` support.
  - If `access_token` is set, it is sent as `Authorization: Bearer`. Otherwise the client loads Google default credentials and refreshes them when expired.
- Credential loading is `load_default_credentials(extra="vertex")`. The project ID falls back to the one in the credentials, or raises `ValueError("Could not resolve project_id")`. The async client runs these blocking auth calls in a separate thread — [SDK source: lib/vertex/_auth.py](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/lib/vertex/_auth.py)
- URL routing in the SDK — [SDK source](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/lib/vertex/_client.py):
  - Messages go to `/projects/{project_id}/locations/{region}/publishers/anthropic/models/{model}:rawPredict`, or `:streamRawPredict` when streaming.
  - `global` → `https://aiplatform.googleapis.com/v1`; `us`/`eu` → `https://aiplatform.{us|eu}.rep.googleapis.com/v1`; other regions → `https://{region}-aiplatform.googleapis.com/v1`.
  - `count_tokens` is supported via `.../models/count-tokens:rawPredict`.
  - Batches raise `AnthropicError("The Batch API is not supported in the Vertex client yet")`.
- Express mode — [Google Cloud – Vertex AI in express mode overview](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/express-mode/overview):
  - "Only the models listed in the preceding table are supported in express mode." That table contains only Gemini models (`gemini-3.1-pro-preview`, `gemini-2.5-flash`, and so on).
  - The key goes in the `x-goog-api-key` header or a `key` query parameter.
  - The page does not mention Claude or partner models, and it does not document a key format.
- Third-party corroboration, not primary: Tailscale's docs say "Anthropic Claude models on Vertex AI use the raw predict endpoint, which requires service account authentication" — [Tailscale Aperture – Vertex AI Express](https://tailscale.com/docs/aperture/how-to/use-vertex-ai-express). A Portkey issue reports that "API Keys only work with Express Mode endpoints", and that standard Vertex endpoints asked for an OAuth 2 access token — [Portkey gateway issue #1441](https://github.com/Portkey-AI/gateway/issues/1441)
- All Python SDK 1.x and 2.x releases require Python 3.10+ and use `httpx2` as the HTTP layer — [SDK MIGRATION.md](https://github.com/anthropics/anthropic-sdk-python/blob/main/MIGRATION.md); [SDK README](https://github.com/anthropics/anthropic-sdk-python)

### Inferences
- Minimal harness client (not run; built from the cited source and docs):
  ```python
  from anthropic import AsyncAnthropicVertex
  vx = AsyncAnthropicVertex(project_id="MY_PROJECT", region="global", max_retries=5)
  # auth: `gcloud auth application-default login` once, or credentials=service_account.Credentials...
  ```
- A service-account JSON works through `GOOGLE_APPLICATION_CREDENTIALS` (standard ADC) or by passing a `google.oauth2.service_account.Credentials` object as `credentials=`. If you pass one explicitly, it may need cloud-platform scopes. That detail is not verified here.
- Do not plan on an `AQ.` express key. The SDK cannot send it. Google documents express mode for Gemini only. Third parties report that `rawPredict` (the Claude endpoint) rejects API keys.

### Gaps
- No Google page explicitly states "Claude/partner models are not supported with API keys". The conclusion rests on Google's Gemini-only express-mode list, the SDK having no api-key path, and third-party reports.
- I did not verify whether Google's newer "API keys bound to a service account" feature for standard (non-express) projects works with `publishers/anthropic` `rawPredict`.

---

## Q3. Tool use on Sonnet 4.6: tool definitions, `tool_choice` none/auto/tool, and the injected (client-written) `tool_use` + `tool_result` history

### Takeaway
Sonnet 4.6 supports custom tools and all four `tool_choice` values (`auto`, `any`, `tool`, `none`) on both the Claude API and Vertex. Forced tool use is blocked only for newer models (Fable 5.x, Mythos 5.x, Opus 5.5, Sonnet 5.5) and with manual extended thinking. The "injected" condition ends with a `user` message that holds the `tool_result`, so it is not assistant prefill. Prefill, which 4.6 models reject, means a request whose *last* message is an assistant message. The docs put no validation on `tool_use` blocks beyond pairing and ordering rules; only *thinking* blocks are signed and checked. The pattern should therefore be accepted. That is an inference; see the Gaps.

### Cited Findings
- Tool definition fields:
  - `name` (regex `^[a-zA-Z0-9_-]{1,128}$`)
  - `description`
  - `input_schema` (JSON Schema)
  - optional `input_examples`
  - other optional properties: `cache_control`, `strict`, `defer_loading`, `allowed_callers`
  - Source: [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- Supported platforms for custom tools include "Claude API: stable" and "Claude Models on Google Cloud (Google managed): stable". `claude-sonnet-4-6` is in the supported-models list — [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- `tool_choice` options, quoted from [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools):
  - "`auto` allows Claude to determine whether to call any provided tools. This is the default value when `tools` are provided."
  - "`any` … must use one of the provided tools."
  - "`tool` forces Claude to always use a particular tool."
  - "`none` prevents Claude from using any tools. This is the default value when no `tools` are provided."
- Forced-tool restrictions — [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools); [API errors – Forced tool use not supported](https://platform.claude.com/docs/en/api/errors):
  - `any` and `tool` fail with manual extended thinking (`thinking: {type: "enabled"}`).
  - They return a 400 on Claude Fable 5.2, Mythos 5.2, Opus 5.5, Sonnet 5.5, Fable 5.1 and Mythos 5.1.
  - Sonnet 4.6 is not on that list.
- Forced-call behaviour — [Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools):
  - "When `tool_choice` is `any` or `tool`, the API makes Claude's response start with a tool call," with no text before the `tool_use` block.
  - "Forcing a tool also skips thinking on every model that accepts forced tool use."
  - Changing `tool_choice` invalidates cached message blocks.
- Tool-use system prompt overhead for Sonnet 4.6: **497 tokens** for `auto`/`none` and **589 tokens** for `any`/`tool`. Haiku 4.5: 496/588. Haiku 5.5: 286/406. "If you provide no `tools`, a tool choice of `none` uses 0 additional system prompt tokens." — [Pricing – Tool use pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- Prefill rule: "Claude 4.6 and later models … do not support prefilling assistant messages. Sending a request with a prefilled last assistant message … returns a 400 `invalid_request_error`". The error message reads: "This model does not support assistant message prefill. The conversation must end with a user message." — [API errors – Prefill not supported](https://platform.claude.com/docs/en/api/errors). Community reports show the same 400 through Vertex — [Google AI dev forum thread](https://discuss.ai.google.dev/t/bug-all-claude-models-fail-with-http-400-assistant-message-prefill-not-supported-via-vertex-ai/136834)
- Pairing and ordering rules — [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls):
  - "Tool result blocks must immediately follow their corresponding tool use blocks in the message history."
  - "In the user message containing tool results, the `tool_result` blocks must come FIRST in the content array. Any text must come AFTER all tool results." Text placed before a `tool_result` is a 400.
  - A missing result produces the error "tool_use ids were found without tool_result blocks immediately after".
  - `tool_result` fields: `tool_use_id`, `content` (a string, or a list of `text`/`image`/`document`/`search_result` blocks), and optional `is_error`.
  - The documented loop: send the follow-up request "with the same `tools` as the first request".
- Validation applies to thinking blocks: "If thinking blocks in the request don't match what the API returned, the request can get a 400 … `thinking` or `redacted_thinking` blocks in the latest assistant message cannot be modified." Nothing similar is documented for `tool_use` blocks — [API errors](https://platform.claude.com/docs/en/api/errors)
- On Sonnet 4.6, omitting `thinking` means "Thinking off" (see Q5), so a synthetic assistant turn has no thinking block to sign — [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- On API version `2026-10-21` only, two more rules apply — [Migration 2026-10-21](https://platform.claude.com/docs/en/api/migration-2026-10-21):
  - A `document` block directly in an `assistant` message is a 400. A document nested in another block is still accepted.
  - A `text` block with non-empty `citations` in a `user` message (including inside a `tool_result`) is a 400.

### Inferences
- Message shapes per condition. These are a recipe derived from the cited docs and were not executed.
  - **Model decides:** send `tools=[read_document]` and `tool_choice={"type":"auto"}`. Next, append the response `content` unchanged as an assistant message, then a user message `[{"type":"tool_result","tool_use_id":tu.id,"content":doc_text}]`.
  - **Forced first call:** use `tool_choice={"type":"tool","name":"read_document"}` on Sonnet 4.6. Fine on 4.6; this would 400 on Sonnet 5.5 or Opus 5.5. Do *not* set `thinking={"type":"enabled",...}` in the same request.
  - **Final answer turn with tools disabled:** keep `tools=[...]` in the request and set `tool_choice={"type":"none"}`. The overhead stays at 497 tokens, the same as `auto`, so the system prompt token count matches between the auto and none turns.
  - **Injected condition:**
    ```python
    messages = [
      {"role": "user", "content": question_text},
      {"role": "assistant", "content": [
          {"type": "tool_use", "id": "toolu_inj_000123", "name": "read_document", "input": {"doc_id": "D42"}}]},
      {"role": "user", "content": [
          {"type": "tool_result", "tool_use_id": "toolu_inj_000123", "content": doc_text},
          {"type": "text", "text": "Now answer ..."}]},  # optional; must come AFTER tool_result
    ]
    ```
    The request ends on a `user` turn, so the prefill rule does not apply. With thinking off, the assistant turn holds only `tool_use`, which is not signed.
- Confound to report in the paper: forced `tool_choice` adds 92 more hidden system prompt tokens than auto/none (589 vs 497 on Sonnet 4.6). Forcing also removes any natural-language preamble.
- To stay compatible with API version `2026-10-21`, send the document as a plain string or a `text` block inside `tool_result` (user side). Do not put `document` blocks in assistant turns or `citations` on user text.
- Keep `tools` defined on every request that contains `tool_use` or `tool_result` blocks. That is the documented pattern ("same `tools` as the first request"). Leaving them out risks a 400 (unverified; see Gaps).

### Gaps
- No Anthropic page explicitly says that client-fabricated `tool_use` blocks (never generated by the model) are accepted. The conclusion is inferred: prefill is defined by the last message; only thinking blocks are signature-checked; tool_use/tool_result rules cover only pairing and order. Run one smoke test per platform before the full run.
- The required `tool_use.id` format is not documented here. Using a `toolu_`-prefixed alphanumeric/underscore ID, as in the example above, is a safe guess, not a verified requirement.
- I did not verify whether a request with tool_use/tool_result history but no `tools` array is rejected, or what the error says.

---

## Q4. Temperature and API version `2026-10-21`: which SDK release switched, how to keep `2023-06-01` so `temperature=0` works on Sonnet 4.6, and how Vertex's `anthropic_version` behaves

### Takeaway
**`anthropic` 2.0.0 (released 2026-10-21) is the first Python SDK release that sends `2026-10-21` by default.** The latest release is 2.13.0, published 2026-11-23. On that version, sending `temperature` at any value returns a 400. Python SDK **1.x** (1.0.0 through 1.17.0) still sends `anthropic-version: 2023-06-01`, and on Vertex it sends `anthropic_version: "vertex-2023-10-16"`. However, 1.x already **removed the `temperature` keyword** (passing it raises `TypeError`), so you must pass `extra_body={"temperature": 0}`. Supported options, simplest first:

- **(A)** Pin `anthropic[vertex]==1.17.0` and pass `extra_body={"temperature": 0.0}`.
- **(B)** Use 2.x and override: on the first-party client, `default_headers={"anthropic-version": "2023-06-01"}`; on Vertex, put `"anthropic_version": "vertex-2023-10-16"` in `extra_body`. In both cases also pass `extra_body={"temperature": 0.0}`.
- **(C)** Pin `0.125.0`, where `temperature=0` still works as a keyword argument.

Anthropic's own migration guide allows keeping a call on `2023-06-01` when it relies on a non-default temperature.

### Cited Findings
- Local reference file (claude-api skill, `shared/api-version-migration.md`, "Set the version"): "Python (`anthropic`) | 2.0.0" is the first release that sends `2026-10-21` by default. Confirmed by the live migration guide: "Upgrade the `anthropic` package to version 2.0.0." — [Migrating to API version 2026-10-21](https://platform.claude.com/docs/en/api/migration-2026-10-21)
- Breaking change: "In `2026-10-21`, a request that sends `temperature`, `top_p`, or `top_k` returns a 400 error, even at the parameter's default value." It applies to Messages, token counting, and each request in a Message Batch created with that version — [Migration 2026-10-21](https://platform.claude.com/docs/en/api/migration-2026-10-21)
- The guide's sanctioned escape: "On models that accept other values, such as Claude Sonnet 4.6, a request that lowered `temperature` for more consistent output loses that effect. No other setting replaces it. If a request relies on a non-default value, either stop sending the parameter, or keep that request on `2023-06-01`." — [Migration 2026-10-21](https://platform.claude.com/docs/en/api/migration-2026-10-21)
- Platforms: `2026-10-21` works on the Claude API and on Google Cloud Vertex AI. On Bedrock it works only for Claude 4.7+ models — [Migration 2026-10-21](https://platform.claude.com/docs/en/api/migration-2026-10-21); local skill file "Platforms" note.
- Vertex body field: "pass `anthropic_version` in the body and not as a header. Set it to `vertex-2023-10-16` or to API version `2026-10-21`." The SDK "sets `anthropic_version` to the API version that it uses with the Claude API" — [Google managed page](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)
- SDK release history — [CHANGELOG.md](https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md); PyPI `info.version` = `2.13.0` on 2026-11-23:
  - **2.0.0 (2026-10-21):** "⚠ BREAKING CHANGES — api: add support for new API version 2026-10-21"
  - **1.17.0 (2026-10-20):** the last 1.x release
  - **1.0.0 (2026-08-20):** "upgrade to httpx2 and some minor breaking changes"
  - **0.125.0 (2026-08-19):** the last 0.x release
  - **2.13.0 (2026-11-23):** latest
- Version constants in the source:
  - `main` (2.x) — [_constants.py](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/_constants.py): `ANTHROPIC_API_VERSION = "2026-10-21"`.
  - `v1.17.0` — [v1.17.0 _constants.py](https://github.com/anthropics/anthropic-sdk-python/blob/v1.17.0/src/anthropic/_constants.py): `ANTHROPIC_API_VERSION = "2023-06-01"`, and the Vertex client has `DEFAULT_VERSION = "vertex-2023-10-16"`.
  - `v0.125.0`: hard-codes `"anthropic-version": "2023-06-01"` and also has `DEFAULT_VERSION = "vertex-2023-10-16"`.
- 1.x removed the sampling keywords: "`temperature`, `top_p`, `top_k` | Remove them … for an older model that still does, pass them through `extra_body`". Example: `client.messages.create(..., model="claude-sonnet-4-6", extra_body={"temperature": 0.2})`. For batches, "put the key straight into the request's `params` dict". — [SDK MIGRATION.md (v1)](https://github.com/anthropics/anthropic-sdk-python/blob/main/MIGRATION.md). Confirmed in source: `v1.17.0` `resources/messages/messages.py` contains no `temperature` parameter, while `v0.125.0` has `temperature: float | Omit = omit`.
- **How the 2.x first-party client builds headers:** `default_headers` returns `{**super().default_headers, "X-Stainless-Async": "false", "anthropic-version": ANTHROPIC_API_VERSION, **self._credential_headers, **self._custom_headers}`. Headers passed by the user are spread *after* the version, so `default_headers={"anthropic-version": "2023-06-01"}` overrides it — [SDK _client.py](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/_client.py)
- **How the 2.x Vertex client sets the body field:** `_prepare_options` does `options.json_data.setdefault("anthropic_version", ANTHROPIC_API_VERSION)`, so a value already present is kept. `_merge_extra_json` "runs before `_prepare_options` so that client hooks, such as Bedrock and Vertex routing, see `extra_body` values". So `extra_body={"anthropic_version": "vertex-2023-10-16"}` survives — [SDK lib/vertex/_client.py](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/lib/vertex/_client.py); [SDK _base_client.py](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/_base_client.py)
- The skill's guidance on overrides: use an override only when the user asks not to upgrade or chooses to keep specific calls on the old version. "On a kept call, a field the upgraded SDK no longer accepts (Python 1.x and later: `temperature`, `top_p`, `top_k`) goes through the SDK's extra-body option." — local skill file `api-version-migration.md`, "Overriding the version"
- Model-side rules for temperature — [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking):
  - Claude Opus 4.7+, Sonnet 5/5.5, **Haiku 5.5**, Fable and Mythos models: "non-default `temperature`, `top_p`, or `top_k` values return a 400 error on every request, regardless of whether thinking is used".
  - "On older models in API versions before `2026-10-21`, the restriction applies only while thinking is on: `temperature` and `top_k` are incompatible with thinking".
  - Result: **Sonnet 4.6 and Haiku 4.5 accept `temperature=0` on `2023-06-01` with thinking off. Haiku 5.5 never accepts `temperature=0`.**
- Message Batches: "Batch results use the API version of the request that created the batch" — [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

### Inferences
- **Option A (lowest risk):**
  ```text
  pip install "anthropic[vertex]==1.17.0"   # sends 2023-06-01 / vertex-2023-10-16
  ```
  ```python
  from anthropic import AsyncAnthropic, AsyncAnthropicVertex
  api = AsyncAnthropic()                                   # ANTHROPIC_API_KEY
  vx  = AsyncAnthropicVertex(project_id="P", region="global")
  kw = dict(model="claude-sonnet-4-6", max_tokens=400, tools=TOOLS,
            tool_choice={"type": "auto"}, messages=msgs,
            extra_body={"temperature": 0.0})              # 1.x has no temperature= kwarg
  r1 = await api.messages.create(**kw)
  r2 = await vx.messages.create(**kw)                       # same model id on Vertex for 4.6
  ```
- **Option B (2.x with overrides):**
  ```python
  api = AsyncAnthropic(default_headers={"anthropic-version": "2023-06-01"})
  vx  = AsyncAnthropicVertex(project_id="P", region="global")
  # first-party call:
  await api.messages.create(..., extra_body={"temperature": 0.0})
  # Vertex call: body field must be overridden per request
  await vx.messages.create(..., extra_body={"anthropic_version": "vertex-2023-10-16", "temperature": 0.0})
  ```
  This rests on reading the source, not on running it. Before scaling up, check with one cheap request (`max_tokens=5`) that no 400 mentions `temperature`. Also log `r._request_id`, or the raw request, to confirm the header.
- Record the exact SDK version and the API version string in the experiment logs, because they determine whether `temperature` is honoured at all.
- Even at temperature 0 there can be some nondeterminism. I did not re-verify a current doc statement on this, so treat repeated-sample variance as an empirical question and measure it.

### Gaps
- I did not find a published end-of-support date for `anthropic-version: 2023-06-01` or `vertex-2023-10-16`. The versioning policy page was not fetched.
- I did not find whether Vertex accepts the body value `"2023-06-01"`, as opposed to `"vertex-2023-10-16"`. The docs name only `vertex-2023-10-16` and `2026-10-21`.
- The overrides in Option B were not executed. They are inferred from SDK source code.

---

## Q5. Thinking: on Sonnet 4.6, does omitting `thinking` mean no thinking? (Plus the judge candidates.)

### Takeaway
Yes. On Sonnet 4.6, leaving out `thinking` means thinking is off. The same holds for Haiku 4.5. **Haiku 5.5 is different:** leaving `thinking` out turns on *adaptive* thinking. To turn it off you must send `thinking={"type":"disabled"}` with effort at `high` or below. Haiku 5.5 also rejects non-default temperature on every request, so it cannot be a temperature-0 judge. Haiku 4.5 can.

### Cited Findings
- Per-model defaults for each `thinking` value (columns: no `thinking` field / `"adaptive"` / `"enabled"` with `budget_tokens` / `"between_tools"` / `"disabled"`) — [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking):
  - **Claude Sonnet 4.6:** Thinking off / Adaptive thinking / Extended thinking (deprecated) / 400 error / Thinking off
  - **Claude Haiku 4.5:** Thinking off / 400 error / Extended thinking / 400 error / Thinking off
  - **Claude Haiku 5.5:** Adaptive thinking / Adaptive thinking / 400 error / 400 error / Thinking off at `high` effort or below
- "On Claude Opus 4.8, Claude Opus 4.7, Claude Opus 4.6, and Claude Sonnet 4.6, thinking is off until you set `thinking: {type: "adaptive"}`." — [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- "Claude Haiku 5.5 also has thinking on by default and accepts `thinking: {type: "disabled"}` at effort `high` or below. At `xhigh` or `max` effort, that combination returns a 400 error … With thinking off, the model can skip a tool call it needs when you also request JSON output." — [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- Haiku 5.5 rejects non-default `temperature`/`top_p`/`top_k` "on every request, regardless of whether thinking is used" — [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- The Messages API heading on the thinking page reads "On by default", which describes newer models. The per-model table above is the authority for 4.6 and earlier — [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- Thinking is supported on Vertex ("Claude Models on Google Cloud (Google managed): stable") — [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)

### Inferences
- For Sonnet 4.6, leave out `thinking` and `output_config`/effort entirely. Then check `all(b.type != "thinking" for b in resp.content)` as a runtime assertion.
- Judge choice:
  - **Haiku 4.5** (`claude-haiku-4-5` on the API, `claude-haiku-4-5@20251001` on Vertex) supports temperature 0 with thinking off on `2023-06-01`. It is the better fit for a deterministic-ish judge.
  - **Haiku 5.5** needs `thinking={"type":"disabled"}` and must run at default temperature. It is cheaper ($0.10/$0.50), but its sampling cannot be held fixed at temperature 0.

### Gaps
- No caveat was found about Sonnet 4.6's default `effort` affecting non-thinking responses. The effort page was not fetched.

---

## Q6. Pricing per 1M tokens (Claude API vs Vertex global/regional) and batch options (first-party Message Batches vs Vertex batch prediction)

### Takeaway
List prices are identical on the Claude API and on Vertex's **global** endpoint:
- Sonnet 4.6: $3 input / $15 output
- Haiku 4.5: $1 / $5
- Haiku 5.5: $0.10 / $0.50 for prompts of 100K tokens or fewer

Vertex regional and multi-region endpoints cost **10% more**: $3.30/$16.50, $1.10/$5.50 and $0.11/$0.55. Batch is **50% off** on both platforms (Sonnet 4.6 batch: $1.50/$7.50). First-party Message Batches take single-turn and multi-turn requests with tools, finish "most… within 1 hour", and expire after 24h. The Vertex *SDK client* cannot submit batches. Vertex batch prediction is a separate Google job: JSONL or BigQuery input, a default limit of 4 concurrent jobs, and per Google's batch page no global endpoint.

### Cited Findings
- **First-party list prices per MTok** (base input / 5m cache write / 1h cache write / cache hit / output) — [Pricing](https://platform.claude.com/docs/en/about-claude/pricing):
  - Sonnet 4.6: $3 / $3.75 / $6 / $0.30 / $15
  - Haiku 4.5: $1 / $1.25 / $2 / $0.10 / $5
  - Haiku 5.5, prompts ≤100K tokens: $0.10 / $0.125 / $0.20 / $0.01 / $0.50
  - Haiku 5.5, prompts >100K tokens: $0.50 / … / $2.50
- **First-party batch prices** (input / output) — [Pricing – Batch processing](https://platform.claude.com/docs/en/about-claude/pricing):
  - Sonnet 4.6: $1.50 / $7.50
  - Haiku 4.5: $0.50 / $2.50
  - Haiku 5.5 (≤100K): $0.05 / $0.25
  - "50 percent discount on both input and output tokens"
- Sonnet 4.6 and earlier models use the previous tokenizer. Claude 4.7+ produce about 30% more tokens for the same text — [Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- Vertex endpoint premium: "Regional and multi-region endpoints include a 10 percent premium over global endpoints." This applies to Sonnet 4.5 / Haiku 4.5 / Opus 4.5 and later models — [Pricing – Cloud platform pricing](https://platform.claude.com/docs/en/about-claude/pricing); [Google managed page](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)
- **Google's Vertex prices**, read from the HTML on 2026-11-23 — [Google Cloud – Partner models pricing](https://cloud.google.com/model-garden/partner-models/pricing):
  - **Global tab:**
    - Sonnet 4.6: input $3.00, output $15.00, batch input $1.50, batch output $7.50, cache hit $0.30
    - Haiku 4.5: $1.00 / $5.00, batch $0.50 / $2.50
    - Haiku 5.5 (≤100K): $0.10 / $0.50, batch $0.05 / $0.25
  - **Regional and multi-region tabs:**
    - Sonnet 4.6: $3.30 / $16.50, batch $1.65 / $8.25
    - Haiku 4.5: $1.10 / $5.50, batch $0.55 / $2.75
    - Haiku 5.5: $0.11 / $0.55
  - `cloud.google.com/vertex-ai/generative-ai/pricing` no longer contains the Claude rows. They live on the Model Garden partner-models pricing page.
- `inference_geo` (the first-party US-only option, 1.1x) is not supported on Vertex — [Pricing – Data residency](https://platform.claude.com/docs/en/about-claude/pricing); local skill `platform-availability.md`
- **First-party Message Batches** — [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing):
  - Limit of "100,000 Message requests or 256 MB" per batch.
  - "most batches completing within 1 hour … Batches expire if processing does not complete within 24 hours." Expired requests are not billed.
  - "Batch results are available for 29 days after creation."
  - "Almost any request you can make to the Messages API can be included in a batch," including tool use and multi-turn conversations.
  - Supported platforms are the Claude API, Claude Platform on AWS, and Claude Models on Google Cloud (**Anthropic** managed). Vertex is not listed.
- The Vertex docs list "Message Batches API" as **not supported** on Claude Models on Google Cloud (Google managed) — [Google managed page](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed). The SDK's Vertex client raises "The Batch API is not supported in the Vertex client yet" — [SDK source](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/lib/vertex/_client.py)
- **Vertex batch prediction** (a Google-native job) — [Google Cloud – Claude batch predictions](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/partner-models/claude/batch):
  - Supports Sonnet 4.6, Haiku 4.5 and Haiku 5.5, among others.
  - Input is BigQuery or JSONL in Cloud Storage, with `custom_id` and a `request` object. The example body has `"anthropic_version": "vertex-2023-10-16"`, `messages` and `max_tokens`.
  - Submit with REST `POST https://LOCATION-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/LOCATION/batchPredictionJobs` or `google-genai` `client.batches.create(model="publishers/anthropic/models/...")`.
  - "By default, the number of concurrent batch requests that you can make in a single project is 4."
  - "The global endpoint for partner models isn't supported."
  - Results are available "after all rows have completed or after 24 hours, whichever comes first."
- Batch API rate limits on the Start tier: 1,000 RPM, 200,000 batch requests in the processing queue, 100,000 per batch. The Message Batches API "isn't subject to ramp limits" — [Rate limits](https://platform.claude.com/docs/en/api/rate-limits)

### Inferences
- Rough cost for Sonnet 4.6, about 11,000 calls per model. Assume about 800 prompt tokens plus 497 tool-system tokens plus about 100 tool-definition tokens, for roughly 1.4K input tokens per call, and 200–400 output tokens:
  - Input: about 15.4M tokens × $3 ≈ **$46**
  - Output: 2.2M–4.4M tokens × $15 ≈ **$33–66**
  - Total ≈ **$80–110** at standard price, or **$40–55** with batch on the API or Vertex global.
  - Haiku 4.5 as judge costs about a third of Sonnet. Haiku 5.5 costs about a thirtieth.
- Batches fit the single-request conditions: auto, forced, none-final and injected, because each is one `messages.create` with a fully specified history. The "model decides then answers" flow needs two dependent rounds, run as two sequential batches. Results arrive within a day.
- On Vertex, batch prediction needs a regional location (for example `us-east5`), so batch traffic pays the 10% regional rate: $1.65/$8.25 for Sonnet 4.6. It also needs the GCS or BigQuery plumbing. For about 11k short calls, synchronous asyncio on the global endpoint ($3/$15) is simpler. Use first-party Message Batches if cost matters.
- Pass `temperature` in batch `params` as a raw key (SDK 1.x) on a batch created with `2023-06-01`. On a `2026-10-21` batch, every such request errors.

### Gaps
- Conflict: Google's pricing page lists batch prices under the **Global** tab, but Google's Claude batch page says "The global endpoint for partner models isn't supported". It is unclear whether global batch is now possible.
- I found no Vertex statement of batch turnaround beyond "24 hours". There is no "most finish within 1 hour" claim for Vertex.
- Google credits and billing: Vertex (Google managed) usage is billed "as Agent Platform usage" on the Google Cloud bill. I did not verify whether education or free-trial credits cover partner-model usage.
- Prompt-caching minimum cacheable lengths for Sonnet 4.6 and Haiku were not re-verified. With 400–1,200-token prompts, caching may not engage, or may not be worth it.

---

## Q7. Rate limits for a new first-party Claude API organization (Sonnet 4.6)

### Takeaway
The first-party tier scheme is now **Evaluation, then Start, then Build, then Scale, then Custom**, with monthly spend caps of $500, $1,000 and $200,000 for Start, Build and Scale. A brand-new organization "may start in the Evaluation tier", whose limits are below the published ones and are not given. On the **Start** tier, Sonnet 4.x (Sonnet 4.6 and 4.5 combined) gets **1,000 RPM, 2,000,000 input TPM and 400,000 output TPM**. Cached reads do not count toward ITPM. "Ramp limits" can also return 429s on sudden bursts.

### Cited Findings
- "New organizations and organizations with limited usage history may start in the Evaluation tier, with limits below the standard limits shown on this page … they increase automatically as your organization builds usage history." — [Rate limits](https://platform.claude.com/docs/en/api/rate-limits)
- Monthly spend caps: Start $500, Build $1,000, Scale $200,000. At the cap, requests return a 429 with `error_code: enforced_spend_limit_reached` and **no `retry-after` header**, until the 1st of the next month — [Rate limits](https://platform.claude.com/docs/en/api/rate-limits)
- **Start tier (RPM / ITPM / OTPM)** — [Rate limits](https://platform.claude.com/docs/en/api/rate-limits):
  - Sonnet 4.x (Sonnet 4.6 and 4.5 combined): 1,000 / 2,000,000 / 400,000
  - Haiku 4.5: 1,000 / 2,000,000 / 400,000
  - Haiku 5.5: 4,000 / 2,000,000 / 400,000
  - Build tier, Sonnet 4.x: 5,000 / 5,000,000 / 1,000,000
  - Scale tier, Sonnet 4.x: 10,000 / 10,000,000 / 2,000,000
- Limits use the token bucket algorithm. "A rate of 60 requests per minute (RPM) might be enforced as 1 request per second." `cache_read_input_tokens` do not count toward ITPM. OTPM counts actual tokens, not `max_tokens` — [Rate limits](https://platform.claude.com/docs/en/api/rate-limits)
- Ramp limits — [Rate limits](https://platform.claude.com/docs/en/api/rate-limits):
  - "After a sharp increase in usage, requests can return a 429 error even while you're under your ITPM and OTPM rate limits." The response has `error_code: ramp_limit_exceeded`.
  - Advice: "Start scheduled or bulk jobs at a low rate and spread requests evenly."
  - Message Batches are exempt.
- The SDK retries 429, 5xx and connection errors twice by default, honouring `retry-after`. Change this with `max_retries` — [API errors](https://platform.claude.com/docs/en/api/errors)
- Response headers include `anthropic-ratelimit-requests-remaining`, `anthropic-ratelimit-input-tokens-remaining`, `anthropic-ratelimit-output-tokens-remaining`, and so on — [Rate limits](https://platform.claude.com/docs/en/api/rate-limits)
- The older "Tier 1–4 with credit-deposit thresholds" scheme does not appear on the current page. It has been replaced by Start/Build/Scale — [Rate limits](https://platform.claude.com/docs/en/api/rate-limits); [Pricing – Rate limits](https://platform.claude.com/docs/en/about-claude/pricing)

### Inferences
- Even on the Start tier, 1,000 RPM and 400K OTPM far exceed what ~11k short calls need. The binding constraints for a new organization are the unknown **Evaluation-tier** limits, **ramp limits**, and the **$500/month Start spend cap**. Sonnet 4.6 at about $80–110 fits under that cap; adding judge runs and retries may not leave much room.
- Start the asyncio worker pool small (for example 4–8 concurrent requests) and increase gradually. Set `max_retries` to around 6–8. Treat `enforced_spend_limit_reached` as fatal; do not retry it.

### Gaps
- No numbers are published for the Evaluation tier. Check the Console's Rate limits page (`platform.claude.com/usage/limits`) after the organization is created.
- Ramp-limit step sizes and starting amounts are not published per model. They "vary by model and can change".
