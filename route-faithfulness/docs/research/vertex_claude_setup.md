> **Snapshot, 23 November 2026.** Research report written before the full run. Two points are out of date: the code is now in [PR #1](https://github.com/dhanushya08/546/pull/1), and measured costs (about $70 Claude, $19 Gemini) replace the estimates below; see [../MODELS_AND_PROVIDERS.md](../MODELS_AND_PROVIDERS.md).

# Run Claude via API, Gemini via Vertex

Tonight's plan works as decided, and the team has tested every part of it in its own Google Cloud project (verified test, 2026-11-23). **`claude-sonnet-4-6` runs on the Claude API** with `anthropic` 2.13.0, the header `anthropic-version: 2023-06-01`, and temperature passed through `extra_body`. **`google/gemini-3.5-flash` runs on Vertex AI's global OpenAI-compatible endpoint**, authenticated with gcloud Application Default Credentials (ADC); `thinking_budget: 0` produced zero reasoning tokens. **`openai/gpt-oss-120b-maas` on Vertex is the judge.** Two other routes are closed for now. Claude on Vertex returns 429 on `global` (zero quota) and 404 on `us-east5` until someone enables the model in Model Garden and gets a quota increase. The team's `AQ.` Google key cannot authenticate to Vertex at all. Llama 3.1 8B/70B and Llama 3.3 70B are no longer in Vertex's managed catalog, so an open-model arm would need Llama 4, a self-deployed endpoint, or another host. The best place to run is a **Colab Enterprise one-off notebook execution**: an e2-standard-2 template with idle shutdown off, the Anthropic key read from Secret Manager, and outputs synced to Cloud Storage. Compute costs about $1. Model calls for C1, C2, T1, C3, C4 and C5 on all 1,880 documents cost about **$65–90 for Sonnet, $30–50 for Gemini and $5–7 for the judge, roughly $110–165 in total** with smoke tests and reruns. The paper must state four things: Google advises against setting temperature on Gemini 3, Google says Gemini 3 thinking cannot be fully disabled, Gemini's T1 rung uses a placeholder thought signature, and Llama 3.1 could not be run on Vertex. One blocker comes first. The harness code for T1, the Claude client and the Vertex client exists only in the local working copy and has not been pushed to GitHub.

## Three models meet the bar of temperature 0, thinking off and tool calls

The experiment needs three things from each model: it accepts temperature 0, it can run without visible reasoning, and it supports `read_document` tool calls in every form the condition ladder uses. As of November 2026, most newly released models fail at least one of these.

**Claude.** Anthropic's newer models reject temperature outright. On Claude Opus 4.7 and later, Sonnet 5/5.5, Haiku 5.5, and the Fable and Mythos models, a non-default `temperature` "return[s] a 400 error on every request, regardless of whether thinking is used" ([Claude docs – Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)). Opus 5.5 and Sonnet 5.5 also return a 400 for forced tool use ([Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)). **Sonnet 4.6 is therefore the newest Claude model that meets all three controls.** It accepts temperature 0 on API versions before `2026-10-21`, and thinking is off unless you request it ([Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)). It supports `tool_choice` values `auto`, `any`, `tool` and `none` ([Define tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)). Its ID is `claude-sonnet-4-6` on both the Claude API and Vertex, because Claude 4.6 and later use the same IDs on Google Cloud ([Claude on Google Cloud, Google managed](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)). Haiku 4.5 is a cheaper fallback that meets the same controls. Haiku 5.5 does not: it turns on adaptive thinking by default and never accepts temperature 0. Sonnet 4.5 is already on Google's partner-model deprecation list ([Partner model deprecations](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/deprecations/partner-models)).

**Gemini.** The pattern is similar. Gemini 3.6, 3.7 and 3.8 Flash accept `temperature` but "the model will ignore them entirely" ([Gemini 3.5 Flash guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-5-flash); [Gemini 3.8 Flash guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash)). Gemini 4 models return a 400 if you set `thinking_budget` ([Gemini thinking](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/thinking)). Gemini 2.5 Flash, the last Gemini that cleanly supported "thinking off at temperature 0", reached its Vertex retirement date on 2026-10-20 ([Model versions and lifecycle](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions)). It now returns 404, even though the OpenAI-compatibility page still lists it (verified test, 2026-11-23). **Gemini 3.5 Flash is the strongest current Gemini that still honours temperature and allows a minimal thinking setting.** It went GA on 19 May 2026, retires no earlier than 19 May 2027, is served on `global`, `us` and `eu`, and supports Chat Completions ([Gemini 3.5 Flash model card](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-flash)).

**Open models.** Vertex's catalog has shrunk. The managed (MaaS) open-model list now contains only DeepSeek-V4.1-Flash, Gemma 4 26B A4B IT, GLM 5.2, gpt-oss 120B, and Llama 4 Scout and Maverick ([Open models for MaaS](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/maas/use-open-models)). Llama 3.3 70B retired on 2026-10-21, together with every Qwen3 MaaS model, DeepSeek V3.x/R1, gpt-oss-20b, GLM 4.7/5, Kimi K2 and MiniMax M2 ([Open model deprecations](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/deprecations/open-models)). Google's current pages do not list Llama 3.1 at all. A third-party notice dates its deactivation to 15 January 2026 ([Portkey](https://new.portkey.ai/announcements/model-deprecation-alert-llama-31-32-on-vertex-ai)). The team's calls to `meta/llama-3.1-8b`, `llama-3.1-70b` and `llama-3.3-70b` all returned 404 (verified test, 2026-11-23).

**The judge.** gpt-oss-120b is a poor *tested* model. It always reasons, and it "doesn't support tool_choice = 'required' or named tool calling" ([Function calling for open models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/capabilities/function-calling)). It works as a *judge*, though: it is cheap, GA, served on `global` ([gpt-oss 120B card](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/openai/gpt-oss-120b)), it is not one of the models being tested, and it returned valid JSON at `reasoning_effort: low` (verified test, 2026-11-23).

| Model (ID as called) | Where | Temp 0 | Thinking off | Tool calls | $/1M in / out | Role tonight |
|---|---|---|---|---|---|---|
| `claude-sonnet-4-6` | Claude API | Yes, on API version `2023-06-01` (verified) | Off by default | auto, any, tool, none | $3 / $15 | **Tested model** |
| `claude-sonnet-4-6` | Vertex `global`, `us-east5`, `europe-west1`, `asia-southeast1` | Yes, with body `anthropic_version: vertex-2023-10-16` | Off by default | Same | $3 / $15 global; $3.30 / $16.50 regional | Blocked: 429 / 404 (verified) |
| `claude-haiku-4-5` (API) / `claude-haiku-4-5@20251001` (Vertex) | Both | Yes | Off by default | Same | $1 / $5 | Cheap fallback |
| `claude-haiku-5-5` | API; Vertex `global`/`us`/`eu` | No (400) | Needs `{"type":"disabled"}` | Same | $0.10 / $0.50 | Fails controls |
| `google/gemini-3.5-flash` | Vertex `global` OpenAI endpoint | Accepted; Google says remove it | `thinking_budget: 0` gives 0 reasoning tokens (verified) | none, auto, required, validated | $1.50 / $9.00 | **Tested model** |
| `google/gemini-3.5-flash-lite` | Vertex `global` | Accepted | Default thinking level MINIMAL | Same | $0.30 / $2.50 | Cheaper backup |
| `google/gemini-3.8-flash` | Vertex `global` | Ignored | Lowest level is LOW | Same | $0.75 / $3.75 (intro) | Fails controls |
| `google/gemini-2.5-flash` | — | — | — | — | — | Retired 2026-10-20; 404 (verified) |
| `openai/gpt-oss-120b-maas` | Vertex `global` | Accepted | Always reasons (`reasoning_effort`) | No `required` or named choice | $0.09 / $0.36 | **Judge** (verified) |
| `meta/llama-4-scout-17b-16e-instruct-maas` / `meta/llama-4-maverick-17b-128e-instruct-maas` | Vertex `us-east5` only (v1beta1 URL, EULA required) | Not documented | Non-reasoning | Function calling | $0.25 / $0.70; $0.35 / $1.15 | Best managed open-model option |
| `google/gemma-4-26b-a4b-it-maas` | Vertex `global` | Not documented | Off by default | Function calling | $0.15 / $0.60 | "Experimental" stage |
| `meta/llama-3.1-8b`, `-70b`, `llama-3.3-70b` MaaS | — | — | — | — | — | Gone; 404 (verified) |

Sources for the table: prices from [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Google partner-model pricing](https://cloud.google.com/model-garden/partner-models/pricing) and [Google-model pricing](https://cloud.google.com/model-garden/pricing). Llama 4 regions and EULA from [Llama 4 Scout](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/llama/llama4-scout) and [Request Llama predictions](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/llama/use-llama). Gemma thinking default from [Thinking for open models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/capabilities/thinking).

### What the team can do if the paper needs an open model

**Llama 4 Scout vs Maverick** is the managed same-family pair. Both have 17B *active* parameters, so the contrast is total capacity (109B vs 400B) and expert count, not dense size.

**Self-deploying Llama 3.1** keeps the original models. Google's vLLM recipe puts 8B on `g2-standard-12` with one L4 GPU at about **$1.15 per node-hour**, and 70B on eight L4s at about **$9.21 per node-hour** ([vLLM serving](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/open-models/vllm/use-vllm); [Agent Platform pricing](https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing)). Tool calls also need vLLM's `--enable-auto-tool-choice --tool-call-parser llama3_json` flags ([vLLM tool calling](https://docs.vllm.ai/en/latest/features/tool_calling.html)).

**Avoid** DeepSeek-V4.1-Flash and GLM 5.2. They are Preview models guaranteed only "until at least" 28 and 30 November 2026 ([DeepSeek-V4.1-Flash card](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/deepseek/deepseek-v41-flash); [GLM 5.2 card](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/zaiorg/glm-52)), so they could disappear in the middle of the run.

## Each provider needs one non-default setting

### Claude: keep the API version at 2023-06-01

**`anthropic` 2.0.0, released 2026-10-21, was the first Python SDK release to send API version `2026-10-21` by default** ([SDK changelog](https://github.com/anthropics/anthropic-sdk-python/blob/main/CHANGELOG.md)). Under that version, "a request that sends `temperature`, `top_p`, or `top_k` returns a 400 error, even at the parameter's default value" ([Migration to 2026-10-21](https://platform.claude.com/docs/en/api/migration-2026-10-21)). The team hit exactly this: SDK 2.13.0 with its default version returned 400 `temperature: Extra inputs are not permitted`. The same SDK with the header overridden to `2023-06-01` and `temperature` sent through `extra_body` worked (verified test, 2026-11-23). `extra_body` is needed because the 1.x and 2.x SDKs removed the `temperature` keyword argument. Anthropic's own migration guide allows this pin: if a request relies on a non-default temperature, "keep that request on `2023-06-01`" ([Migration to 2026-10-21](https://platform.claude.com/docs/en/api/migration-2026-10-21)).

The harness already does this in `src/llm_anthropic.py` (header for the Claude API; body field `anthropic_version: vertex-2023-10-16` for Vertex). One change is still needed. `requirements.txt` allows any `anthropic[vertex]>=2.0,<3`, but the behaviour depends on the exact version, so **pin `anthropic[vertex]==2.13.0`** and record it in the run log.

```yaml
# config.yaml (already present)
claude_sonnet46:
  provider: anthropic
  model: claude-sonnet-4-6
  api_key_env: ANTHROPIC_API_KEY
  anthropic_version: "2023-06-01"     # 2026-10-21 rejects temperature
```

```python
# What the harness sends, in raw SDK terms (verified test, 2026-11-23)
client = anthropic.AsyncAnthropic(default_headers={"anthropic-version": "2023-06-01"})
r = await client.messages.create(model="claude-sonnet-4-6", max_tokens=400,
        tools=[READ_DOCUMENT], tool_choice={"type": "auto"}, messages=msgs,
        extra_body={"temperature": 0})          # no `thinking` field = thinking off on Sonnet 4.6
```

**T1 on Claude needs no special handling.** The injected rung is a user turn, then a harness-written assistant `tool_use`, then a user `tool_result`. Because the history ends on a user turn, the rule that "Claude 4.6 and later models … do not support prefilling assistant messages" does not apply ([API errors](https://platform.claude.com/docs/en/api/errors)). Anthropic signs only *thinking* blocks, so a fabricated `tool_use` block has nothing to fail validation against. The team confirmed that this history is accepted with `tool_choice: {"type": "none"}` (verified test, 2026-11-23). The `tool_result` block must come first in its user message; any text goes after it ([Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

```python
# T1 for Claude: client-written call, then the verbatim document
[{"role": "user", "content": c3_user_text},
 {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_t1_0001",
                                    "name": "read_document", "input": {"doc_id": "D42"}}]},
 {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_t1_0001",
                               "content": document_text}]}]
```

**Whenever `tools` are present, Claude adds a hidden tool-use system prompt.** For Sonnet 4.6 it is **497 tokens** with `auto` or `none` and **589 tokens** with `any` or `tool`. It adds nothing when the request has no tools ([Claude pricing – tool use](https://platform.claude.com/docs/en/about-claude/pricing)). So T1 and C3 carry about 500 tokens of hidden instructions that C1, C2, C4 and C5 do not.

### Gemini: ADC token, thinking budget, thought signatures

**Endpoint and auth.** The endpoint is `https://aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/global/endpoints/openapi`. The `api_key` is an ADC OAuth access token, which expires after about an hour ([Authenticate with OpenAI libraries](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/migrate/openai/auth-and-credentials)). The harness refreshes the token a few minutes before it expires (`src/llm.py`), so multi-hour runs are covered.

**Thinking.** `thinking_budget: 0` produced **zero reasoning tokens** (verified test, 2026-11-23). It has to be passed with the doubly nested `extra_body` form documented for the Python SDK ([OpenAI examples](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/migrate/openai/examples)). Google's documentation disagrees with that result in tone. It says "You can't turn off thinking or disable thought_signature generation for Gemini 3 and later models" ([Thought signatures](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/thinking/thought-signatures)), and that `thinking_budget` on Gemini 3 "can cause intermittent 400" errors ([Gemini thinking](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/thinking)). The working position is: **keep `thinking_budget: 0`, log reasoning tokens on every row, and watch for 400s.** If they appear, the documented fallback is `reasoning_effort: "minimal"`, which "matches the 'no thinking' setting for most queries" ([Gemini 3.5 Flash guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-5-flash)). Do not combine the two settings; only one of `reasoning_effort` or `thinking_config` may be set ([Using OpenAI libraries](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/migrate/openai/overview)).

```python
creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
creds.refresh(google.auth.transport.requests.Request())
client = AsyncOpenAI(api_key=creds.token,
    base_url=f"https://aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/global/endpoints/openapi")
r = await client.chat.completions.create(model="google/gemini-3.5-flash", messages=msgs,
        tools=[READ_DOCUMENT_FN], temperature=0, max_tokens=400,
        extra_body={"extra_body": {"google": {"thinking_config": {"thinking_budget": 0}}}})
```

**Tool choice.** The supported values are `none`, `auto`, `required` (ANY) and the Google-specific `validated`. The named-function object is not documented, and "if you pass any unsupported parameter, it is ignored" ([Using OpenAI libraries](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/migrate/openai/overview)). Keep `run.force_tool_call: false`. If forcing is ever needed, use `"required"`: with a single tool it has the same effect as naming it.

**Thought signatures.** Gemini 3 enforces them on every function call in the history. When the team echoed a model's own tool call back *without* `extra_content.google.thought_signature`, it got a 400 (verified test, 2026-11-23). The harness copies these provider fields from the response (`model_extra` in `src/llm.py`), so C3's real calls round-trip intact. T1's call was written by the harness and has no real signature, so it uses Google's placeholder `skip_thought_signature_validator`, which the team confirmed is accepted (verified test, 2026-11-23). Google describes this placeholder as a last resort that can reduce quality ([Thought signatures](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/thinking/thought-signatures)). That makes it a methodological caveat (see the final section).

```python
# T1 for Gemini: same structure as Claude's, plus the placeholder signature
{"role": "assistant", "content": None, "tool_calls": [{"id": "t1-read-0001", "type": "function",
   "function": {"name": "read_document", "arguments": "{\"doc_id\": \"D42\"}"},
   "extra_content": {"google": {"thought_signature": "skip_thought_signature_validator"}}}]},
{"role": "tool", "tool_call_id": "t1-read-0001", "content": document_text}
```

**Temperature.** The harness sends `temperature: 0` to Gemini as well. The 3.5 Flash card still lists a 0.0–2.0 range ([3.5 Flash card](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-flash)). Google's Gemini 3 guidance, however, says temperature, top_p and top_k are "no longer recommended … Remove these parameters from all requests" ([Gemini 3.5 Flash guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-5-flash)). The team accepts that deviation risk so that sampling stays matched with Claude.

### The judge: low effort and room for reasoning

The judge entry (`provider: vertex_openai`, `model: openai/gpt-oss-120b-maas`, `extra_body: {reasoning_effort: low}`) uses the same endpoint and ADC token as Gemini. gpt-oss puts its reasoning in a separate `reasoning_content` field ([Thinking for open models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/capabilities/thinking)), and those reasoning tokens count against `max_tokens`. That is why the config raises the judge's `max_tokens` to 1,000 while answers stay capped at 400.

## ADC, one API key and a zero quota gate the setup

**Naming first.** Google renamed Vertex AI to "Gemini Enterprise Agent Platform" in April 2026 ([Campus Technology](https://campustechnology.com/articles/2026/05/04/google-intros-new-gemini-enterprise-agent-platform.aspx)). Consoles and docs now say "Agent Platform", but the API host `aiplatform.googleapis.com`, the `/endpoints/openapi` path and role IDs such as `roles/aiplatform.user` are unchanged ([Vertex deprecations banner](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/deprecations)).

**Credentials.** The run uses one credential per platform. The **Claude API key** (`ANTHROPIC_API_KEY`) is the only secret. Everything on Vertex (Gemini, the judge, and Claude on Vertex later) uses **ADC**. The `Async(Anthropic)Vertex` client does not even have an `api_key` parameter ([SDK source](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/lib/vertex/_client.py)). Google states that "Only Google Cloud Auth is supported using the OpenAI library" ([OpenAI compatibility](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/openai)). Express-mode keys cover only `generateContent` on a short list of Gemini models ([Express mode overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/express-mode/overview)).

**The `AQ.` key.** This explains why the team's `AQ.` key was rejected by Vertex but accepted by the Gemini Developer API at `generativelanguage.googleapis.com` (verified test, 2026-11-23). The `gemini35_flash_apikey` config entry works as an emergency fallback for Gemini. It is a different service with its own quotas and billing, though, so any results from it must be labelled as Gemini Developer API in the paper, not Vertex.

**Where ADC comes from.** ADC looks for credentials in a fixed order: `GOOGLE_APPLICATION_CREDENTIALS`, then the file written by `gcloud auth application-default login`, then the attached service account ([How ADC works](https://docs.cloud.google.com/docs/authentication/application-default-credentials)). Which identity the harness gets therefore depends on where it runs:

- **Laptop:** the student's own login. Set a quota project to avoid "no quota project" errors with user credentials ([Troubleshoot ADC](https://docs.cloud.google.com/docs/authentication/troubleshoot-adc)).
- **Colab Enterprise:** your user credentials. "By default Colab Enterprise notebooks use your user credentials," with end-user credentials (EUC) on in the default runtime ([Colab introduction](https://docs.cloud.google.com/colab/docs/introduction)).
- **Workbench:** the instance's service account, which needs the roles itself ([Manage access to JupyterLab](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/manage-access-jupyterlab)).

**IAM.** Every caller needs `roles/aiplatform.user`, which carries `aiplatform.endpoints.predict`. Whoever enables Claude or a Llama MaaS model in Model Garden needs `roles/consumerprocurement.entitlementManager`. The org policy must also allow `cloudcommerceconsumerprocurement.googleapis.com` ([Use partner models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/use-partner-models)). One check matters for a university project: "If your Google Cloud billing account is managed by a prohibited reseller, you will be unable to accept the Terms of Service or enable Claude models" (same source).

```bash
# One-time project setup (placeholders in caps; Secret Manager syntax is standard gcloud, not re-verified)
gcloud config set project PROJECT_ID
gcloud services enable aiplatform.googleapis.com compute.googleapis.com dataform.googleapis.com \
  secretmanager.googleapis.com cloudcommerceconsumerprocurement.googleapis.com
for ROLE in roles/aiplatform.user roles/aiplatform.colabEnterpriseUser roles/serviceusage.serviceUsageConsumer; do
  gcloud projects add-iam-policy-binding PROJECT_ID --member=user:STUDENT_EMAIL --role=$ROLE; done
gcloud projects add-iam-policy-binding PROJECT_ID --member=user:LEAD_EMAIL \
  --role=roles/consumerprocurement.entitlementManager          # only whoever enables Claude
printf %s "$ANTHROPIC_API_KEY" | gcloud secrets create anthropic-api-key --data-file=- --replication-policy=automatic
gcloud secrets add-iam-policy-binding anthropic-api-key --member=user:STUDENT_EMAIL \
  --role=roles/secretmanager.secretAccessor
# Local runs only
gcloud auth application-default login
gcloud auth application-default set-quota-project PROJECT_ID
```

### Unblocking Claude on Vertex later

Claude on Vertex needs two separate fixes, and neither should hold up tonight's run.

**Enablement.** Open the Claude Sonnet 4.6 card in Model Garden and enable it. Google says "To access a Claude on Google Cloud model, go to its Model Garden model card" ([Claude on Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude)). The 404 on `us-east5` is consistent with the model not yet being enabled for the project. That is an inference, not a confirmed diagnosis.

**Quota.** The quota is the clearer problem. Google's published default for Sonnet 4.6 on `global` is **1,500 QPM, 1.5M input TPM and 150K output TPM** ([Claude quotas](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude/quotas)). The team's project instead effectively had **zero** `global_online_prediction_requests_per_base_model` quota (verified test, 2026-11-23). The documented figure is therefore what to *request* on the **Quotas & System Limits** page (filter by `base_model`), not what a new project gets. The global endpoint and each multi-region endpoint have separate quota buckets. At concurrency 8 and a few seconds per call, the harness sends roughly 100–160 requests per minute, so a grant of about 200 QPM on `global` is enough.

**After both fixes,** switch to the existing `claude_sonnet46_vertex` entry (`region: global`, `anthropic_version: vertex-2023-10-16`). That path has not been tested end to end, so smoke-test it before relying on it. The price matches the Claude API on `global` ($3/$15); regional endpoints cost 10% more. The Vertex client cannot submit Message Batches ([Claude on Google Cloud, Google managed](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed)).

## A Colab Enterprise one-off execution keeps running when the laptop closes

Both Google notebook products can run this CPU-only, network-bound job. They differ in the details that matter for a run lasting several hours.

| | Colab Enterprise | Workbench |
|---|---|---|
| Idle shutdown | 180 min default; set only when creating a runtime template; `0s` disables it ([Colab idle shutdown](https://docs.cloud.google.com/colab/docs/idle-shutdown)) | 180 min default; can be changed later; **CPU use does not reset the timer** ([Workbench idle shutdown](https://docs.cloud.google.com/vertex-ai/docs/workbench/instances/idle-shutdown)) |
| Identity seen by ADC | Your user (EUC on by default) | Instance service account |
| GitHub | Import only (from your computer, Cloud Storage or a URL); no push ([Colab quickstart](https://docs.cloud.google.com/colab/docs/create-console-quickstart)) | JupyterLab Git: clone, commit, push ([Save to GitHub](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/save-to-github)) |
| Headless long runs | One-off execution, default timeout 24h, output to Cloud Storage ([gcloud colab executions create](https://docs.cloud.google.com/sdk/gcloud/reference/colab/executions/create)) | `tmux` with idle shutdown off, or the scheduled executor |
| Cost, e2-standard-2 | About $0.09/h with a 50 GiB balanced disk ([Colab pricing](https://cloud.google.com/colab/pricing)) | About $0.08/h compute, plus about $9–10/month for disks while the instance exists ([platform pricing](https://cloud.google.com/vertex-ai/pricing)) |

**Colab Enterprise is the better fit tonight.** A one-off execution keeps running after the browser closes, writes the executed notebook to Cloud Storage, and runs with the student's own credentials, so no service account is needed ([Schedule a notebook run](https://docs.cloud.google.com/colab/docs/schedule-notebook-run)).

**Git workflow.** Colab Enterprise has a real limitation here. It stores notebooks as Dataform-backed assets with no GitHub link, and a Google reply in 2024 said opening notebooks from GitHub was "currently not available" ([Google Developer forums](https://discuss.google.dev/t/colab-enterprise-cloning-github-repos-and-opening-notebooks/145153)). Keep GitHub as the source of truth and make the base-config notebook a **thin launcher** that clones the repo and runs the CLI. The current commit (`712f3ae`) has no notebook, so commit one and then copy it to Cloud Storage to run it.

**Push the harness changes first.** `git status` shows `src/llm_anthropic.py` as untracked, and `config.yaml`, `src/llm.py`, `src/conditions.py` and `src/prompts.py` as modified but not committed. A cloud clone of `main` would therefore have no T1, no Claude client and no Vertex client.

**Two further gaps in a fresh clone.** `data/*.jsonl`, `outputs/` and `results/` are all gitignored, so a fresh runtime has to rebuild the data (`python -m src.data --prepare`) or pull it from Cloud Storage. And since 2026-11-09, Colab templates set to "latest" create **Python 3.13** runtimes ([Colab release notes](https://docs.cloud.google.com/colab/docs/release-notes)), while the team has developed on 3.12. Run the 30-pair smoke test on the real runtime before the full run.

```bash
# Runtime template (EUC and internet access are on by default) and headless launch
gcloud colab runtime-templates create --display-name=cs546-cpu --region=us-central1 \
  --machine-type=e2-standard-2 --disk-type=PD_BALANCED --disk-size-gb=50 --idle-shutdown-timeout=0s
gcloud storage cp notebooks/base_config.ipynb gs://BUCKET/notebooks/
gcloud colab executions create --display-name=route-faithfulness --region=us-central1 \
  --notebook-runtime-template=TEMPLATE_ID --gcs-notebook-uri=gs://BUCKET/notebooks/base_config.ipynb \
  --gcs-output-uri=gs://BUCKET/executions --user-email=STUDENT_EMAIL --execution-timeout=12h
```

**Secrets.** Colab Enterprise has no documented equivalent of consumer Colab's Secrets panel. The official `/colab/docs/secrets` page returns 404, and community guidance points to Secret Manager ([Medium, Google Cloud community](https://medium.com/google-cloud/using-api-keys-and-other-sensitive-data-in-a-colab-notebook-c2feba57c4e0)). The notebook should load the key into the environment without printing it ([Access a secret version](https://docs.cloud.google.com/secret-manager/docs/access-secret-version)).

**Durable outputs.** The execution's disk disappears when the run ends, so the launcher syncs outputs to Cloud Storage every ten minutes. It also pulls existing outputs down first, so the harness's resume logic (which also retries rows that errored) works across executions.

```python
PROJECT, BUCKET = "PROJECT_ID", "gs://BUCKET/route-faithfulness"
MODELS = ["claude_sonnet46", "gemini35_flash"]
!git clone --depth 1 https://github.com/dhanushya08/546.git
%cd 546/route-faithfulness
!pip install -q -r requirements.txt "anthropic[vertex]==2.13.0" google-cloud-secret-manager

import os, subprocess, threading, time
from google.cloud import secretmanager
os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT        # Vertex calls use the runtime's ADC (EUC)
os.environ["ANTHROPIC_API_KEY"] = secretmanager.SecretManagerServiceClient().access_secret_version(
    name=f"projects/{PROJECT}/secrets/anthropic-api-key/versions/latest").payload.data.decode()

!gcloud storage rsync --recursive {BUCKET}/data data || python -m src.data --prepare
!gcloud storage rsync --recursive {BUCKET}/outputs outputs || true

def sync():                                          # durable checkpoint every 10 minutes
    while True:
        time.sleep(600)
        subprocess.run(["gcloud", "storage", "rsync", "--recursive", "outputs", f"{BUCKET}/outputs"])
threading.Thread(target=sync, daemon=True).start()

procs = [subprocess.Popen(["python", "-m", "src.run", "--model", m]) for m in MODELS]   # both in parallel
assert all(p.wait() == 0 for p in procs)
for m in MODELS:
    subprocess.run(["python", "-m", "src.judge", "--model", m], check=True)
subprocess.run(["python", "-m", "src.analyze"], check=True)
!gcloud storage rsync --recursive outputs {BUCKET}/outputs
!gcloud storage rsync --recursive results {BUCKET}/results
```

**Alternatives.** On Workbench, run the same commands in `tmux` from the JupyterLab terminal. Turn idle shutdown off with `--metadata=idle-timeout-seconds=` (an empty value), because terminal jobs do not count as kernel activity. Give the instance's service account `roles/aiplatform.user` and `roles/secretmanager.secretAccessor`, and stop the instance afterwards, since its disks keep billing. A laptop run with local ADC also works, because the harness resumes where it stopped. It just needs the machine to stay awake for the two to four hours per model that the README estimates (on macOS, `caffeinate -i`).

## Tonight's run costs about $110–165; six caveats belong in the paper

**Call volume.** Six conditions on 1,880 documents give **11,280 answers per model**. C3 adds a tool-call turn per document, so there are about **13,160 model calls** per model.

**Token assumptions.** FaithConflict documents average **2,124 characters (about 290 words, roughly 500 tokens)**, measured from the team's `data/faithconflict.jsonl`. Per document, input totals about 6,700 tokens for Claude across the six conditions. C5 carries three retrieved documents, and T1 and C3 carry the 497-token hidden tool prompt. Output is assumed at 150–300 tokens per answer under the 400-token cap. The judge is about 1,500 input tokens per call, with 300–500 output tokens of low-effort reasoning plus JSON.

| Item | Volume (estimate) | List price per 1M tokens | Cost |
|---|---|---|---|
| `claude-sonnet-4-6`, Claude API | ~12.6M in, 1.8–3.5M out | $3 / $15 ([pricing](https://platform.claude.com/docs/en/about-claude/pricing)) | **$65–90** |
| `google/gemini-3.5-flash`, Vertex global | ~10–11M in, 1.8–3.5M out (reasoning ≈ 0) | $1.50 / $9.00 ([pricing](https://cloud.google.com/model-garden/pricing)) | **$30–50** |
| Judge `openai/gpt-oss-120b-maas` | 22,560 calls; ~34M in, 7–11M out | $0.09 / $0.36 ([pricing](https://cloud.google.com/model-garden/partner-models/pricing)) | **$5–7** |
| Colab Enterprise runtime | e2-standard-2 + 50 GiB balanced disk, ~12 h | ~$0.09/h ([Colab pricing](https://cloud.google.com/colab/pricing)) | **~$1** |
| Smoke tests and reruns | 30 pairs per model, plus about 5–10% retries | — | **$5–15** |
| **Total** | | | **~$110–165** (budget $175) |

**Cheaper levers exist, but none suits tonight.** Claude Message Batches cost half price ([Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)), which would bring Sonnet down to about $33–45. However, the harness runs synchronously, and C3 and T1 need dependent rounds. Haiku 4.5 costs a third as much as Sonnet but is a different model. Claude on Vertex's `global` endpoint costs the same list price as the Claude API.

**Rate limits are not the binding constraint.** The Claude API's Start tier allows Sonnet 4.x **1,000 RPM, 2M input TPM and 400K output TPM**. Brand-new organisations, however, "may start in the Evaluation tier" with unpublished, lower limits, and sudden bursts can trigger `ramp_limit_exceeded` 429s ([Rate limits](https://platform.claude.com/docs/en/api/rate-limits)). The Start tier's **$500/month spend cap** comfortably covers this run. Gemini's Standard PayGo Tier 1 gives Flash models 2M TPM on the global endpoint ([Standard PayGo](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/standard-paygo)), far above the roughly 50–100K TPM this run generates. The harness's default concurrency of 8, with retries and exponential backoff up to 60 seconds, is appropriate for both providers.

**Open risks before launch:**

| Risk | Evidence | Mitigation |
|---|---|---|
| Cloud clone runs the old harness | T1, Claude and Vertex code is uncommitted (`git status`) | Commit and push before any Colab or Workbench run |
| Gemini 3 returns intermittent 400s with `thinking_budget` | Documented ([Gemini thinking](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/thinking)) | The harness treats 400 as fatal for that row; rerun to retry errored rows. If errors persist, switch to `reasoning_effort: minimal` and report the switch |
| Unknown Claude limits for a new org | Evaluation tier limits are unpublished ([Rate limits](https://platform.claude.com/docs/en/api/rate-limits)) | Start at concurrency 8 and check Console → Limits after the smoke test |
| Legacy API version is retired | No end-of-support date found for `2023-06-01` | Pin SDK 2.13.0; log the SDK version and API version string with every run |
| Python 3.13 on Colab | [Colab release notes](https://docs.cloud.google.com/colab/docs/release-notes) | Run the 30-pair smoke test on the actual runtime |
| Parameters silently ignored on Vertex | "unsupported parameter … is ignored" ([Using OpenAI libraries](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/migrate/openai/overview)) | Assert on outputs: reasoning tokens = 0, tool-call rate in C3, no thinking blocks from Claude |

**Methodological caveats to state in the paper:**

| Caveat | What to write |
|---|---|
| Temperature | Claude ran at temperature 0 by pinning the legacy API version `2023-06-01`, because the current version rejects any temperature. Gemini 3.5 Flash accepted temperature 0, but Google advises removing sampling parameters for Gemini 3 ([guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-5-flash)). Neither setting guarantees determinism, so report a repeat-sample check on a subset. |
| Thinking | Claude ran with thinking off, which is the default when no `thinking` field is sent. Gemini ran with `thinking_budget: 0` and logged 0 reasoning tokens, but Google states that Gemini 3 thinking cannot be fully disabled and that signatures are still enforced. Report reasoning-token counts per condition. |
| Placeholder signature in T1 | Gemini's injected T1 call uses `skip_thought_signature_validator`, which Google calls a last resort that can reduce quality ([Thought signatures](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/thinking/thought-signatures)). Claude's T1 needs no equivalent. Gemini's C2→T1 and T1→C3 contrasts therefore mix the channel and agency effects with a platform artifact. Report them per model, and flag Gemini's T1 separately. |
| Hidden tool prompt | Whenever tools are defined (T1, C3), Claude prepends a 497-token tool-use system prompt; C1, C2, C4 and C5 get none ([pricing](https://platform.claude.com/docs/en/about-claude/pricing)). This counts as part of "the tool channel" and should be named. |
| Llama 3.1 unavailable | Llama 3.1 8B/70B and Llama 3.3 70B are no longer served as Vertex MaaS (404 in the team's tests; [deprecations](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/deprecations/open-models)). Any open-model arm used another host, self-deployment, or Llama 4 Scout/Maverick, which share 17B active parameters. |
| Judge and platforms | The judge, gpt-oss-120b, is a reasoning model run at `reasoning_effort: low` and is neither tested model. Its agreement with humans is reported as Cohen's kappa (README step 5). The two tested models were served from different platforms (Claude API and Vertex AI) on dated runs, because neither Sonnet 4.6 nor Gemini 3.5 Flash is pinned to a dated snapshot ID. |

## Conclusion

The main lesson is that **"temperature 0, thinking off" is no longer a default setting. On every provider it takes a deliberate workaround**, and each workaround has a shelf life. Anthropic has removed temperature from its current API version and its newest models. Google ignores temperature on Gemini 3.6 and later, and says thinking cannot be fully disabled on any Gemini 3 model. Sonnet 4.6 and Gemini 3.5 Flash are close to the last models where the experiment's controls can still be honoured, so the paper should give the exact SDK version, API version string, endpoint and run date as part of the method. Reviewers should treat them like random seeds: without them the run cannot be reproduced.

The T1 rung is the most informative and the most fragile part of the design. It cleanly separates channel from agency on Claude, but on Gemini it requires a placeholder that Google itself flags as quality-reducing. A T1 effect that shows up on Claude but not on Gemini is therefore ambiguous until a follow-up rules out the placeholder. Running the identical ladder on Claude on Vertex, once the quota is granted, would also be worthwhile. It would show whether the serving platform alone moves faithfulness, at no extra list price.
