# Models and providers

Claude Sonnet 4.6 runs through the Claude API and Gemini 3.5 Flash through Vertex AI. The judge, gpt-oss-120b, also runs on Vertex AI. Everything below was tested on 2026-11-23; the research behind the choices, with sources, is in [research/vertex_claude_setup.md](research/vertex_claude_setup.md).

## What runs where

| Config key | Model | Route | Auth | Status |
|---|---|---|---|---|
| `claude_sonnet46` | `claude-sonnet-4-6` | Claude API, Anthropic SDK | `ANTHROPIC_API_KEY` in `.env` | Works; full run in progress |
| `gemini35_flash` | `google/gemini-3.5-flash` | Vertex AI OpenAI-compatible endpoint, `global` | gcloud ADC | Works; full run answered |
| judge | `openai/gpt-oss-120b-maas` | Vertex AI, `global` | gcloud ADC | Works |
| `gemini35_flash_apikey` | `gemini-3.5-flash` | Gemini Developer API | `GEMINI_API_KEY` | Works; same model without gcloud |
| `claude_sonnet46_vertex` | `claude-sonnet-4-6` | Claude on Vertex AI | gcloud ADC | Blocked: quota is 0 |
| `gpt4o` | `gpt-4o-2024-08-06` | OpenAI | `OPENAI_API_KEY` | Configured, not run (no key yet) |
| `qwen35_9b_vllm`, `gemma4_12b_vllm` | self-hosted | vLLM on Delta / Colab | none | Unchanged from before |

The `provider:` field on each model picks the client (`src/llm.py`): `openai` (default, any OpenAI-compatible API), `vertex_openai`, `anthropic`, `anthropic_vertex`.

## What does not work, and why

| Tried | Result | Why | Way forward |
|---|---|---|---|
| Claude Sonnet 4.6 on Vertex, `global` | 429 quota exceeded | New projects get 0 requests per minute for Claude | Enable it in Model Garden and request `global_online_prediction_requests_per_base_model`; or keep using the Claude API |
| Claude Sonnet 4.6 on Vertex, `us-east5` | 404 | Not enabled for the project | Same |
| A Google `AQ.` API key on Vertex AI | 401 / 403 | Vertex's OpenAI-compatible endpoint takes only OAuth (gcloud ADC); that key is a Gemini Developer API key | Use gcloud ADC for Vertex, or `gemini35_flash_apikey` with the key |
| `google/gemini-2.5-flash` on Vertex | 404 | Retired 2026-10-20 | Gemini 3.5 Flash |
| `meta/llama-3.1-8b`, `-70b`, `llama-3.3-70b` MaaS | 404 | No longer in Vertex's managed catalog | Llama 3.1 via vLLM (README section 10, about $1.15/hour for 8B on one L4); or Llama 4 Scout / Maverick MaaS (us-east5, both 17B active) |
| gpt-oss-120b as a tested model | not used | Always reasons; no `required` or named `tool_choice` | Fine as the judge |

## Provider quirks the code handles

| Quirk | Symptom | Handling |
|---|---|---|
| Anthropic SDK 2.x sends API version `2026-10-21`, which rejects `temperature` | 400 "temperature: Extra inputs are not permitted" | `src/llm_anthropic.py` pins `anthropic-version: 2023-06-01` and sends temperature 0 in `extra_body`. Sonnet 4.6 is the newest Claude that accepts temperature 0; later models only accept the default |
| Gemini 3 needs each tool call's `thought_signature` echoed back | 400 on the second turn of C3 | `src/llm.py` keeps the call's `extra_content` when it builds the history |
| T1's tool call is written by the harness, so it has no signature | 400 on every T1 request | `injected_tool_call_extra` in `config.yaml` adds Google's placeholder `skip_thought_signature_validator` |
| Gemini thinks by default | Reasoning tokens in usage | `thinking_budget: 0` in `extra_body`; `reasoning_present` flags any answer that still reasoned (2 of 1,880 in T1) |
| Vertex access tokens expire after about an hour | 401 mid-run | The OpenAI client asks a refresher for the token on each request (tested with a forced expiry) |
| Gemini sometimes returns a choice with no message | Crash | Retried as transient; if `finish_reason` is `malformed_response` (the model's own broken tool call, repeats on retry), it is logged as an empty answer, route event R5 |
| gpt-oss nests its JSON | `{"final": {"code": ...}}` read as unparseable | `parse_code` in `src/judge.py` finds the code anywhere in the reply |

## How the full run behaved (Gemini 3.5 Flash, all 940 pairs)

- 0 API errors across 11,280 documents; the full run took 33 minutes at concurrency 16.
- C3: the tool was called on 1,880 of 1,880 documents.
- **C3: 69 empty answers (3.7%), all malformed tool calls on the model's second turn.** They cluster on safety content: 25 of 386 safety-opposing and 17 of 386 safety-confirming, against 5 of 496 capability documents. Until the team decides (TEAM_GUIDE task 3), these have no label and drop out of the faithful rates.
- T1: 22 empty answers (1.2%), finish reason `stop`; the model called the tool again 4 times after the injected read.
- C5: BM25 recall@3 92% (1,736 of 1,880).
- Repeating one T1 request gave two different answers at temperature 0, so Gemini is not deterministic.

## Costs

| Model | Price, $ per 1M tokens (input / output) | Full run, 6 conditions × 1,880 documents |
|---|---|---|
| Claude Sonnet 4.6 (Claude API) | 3.00 / 15.00 | About $70 projected ($43.52 at 7,201 documents) |
| Gemini 3.5 Flash (Vertex) | 1.50 / 9.00 | $18.99 measured (6.47M input, 1.03M output tokens) |
| gpt-oss-120b judge (Vertex) | 0.09 / 0.36 | About $4 per model, estimated |
| Notebook runtime on Colab Enterprise (e2-standard-2) | about $0.10 per hour | About $1 for a night |

The notebook's smoke-test section estimates a full run's cost from real token counts before you start it. Cheaper alternatives that meet the same controls: Claude Haiku 4.5 ($1 / $5) and Gemini 3.5 Flash-Lite ($0.30 / $2.50).

## Caveats to state in the paper

- **Temperature.** Claude runs at temperature 0 only on the older API version `2023-06-01`. Google calls temperature "not recommended" on Gemini 3, and Gemini answered the same request differently twice.
- **Thinking.** Gemini logged 0 reasoning tokens with `thinking_budget: 0` (2 exceptions in 1,880 T1 answers), although Google says Gemini 3 thinking cannot be fully disabled.
- **T1 on Gemini** uses a placeholder thought signature, which Google calls a last resort; C3's calls carry the model's own. Part of Gemini's C2→T1 and T1→C3 steps could come from this.
- **Claude's hidden tool prompt.** When tools are sent, Anthropic adds a tool-use system prompt (about 500 tokens) that C1 and C2 never see. That is part of the "channel" in T1.
- **Empty answers** are not random: Gemini's malformed tool calls cluster on safety documents.
- **Different platforms.** Claude and Gemini run on different providers, and the judge is a reasoning model.
- **Llama 3.1** could not be run on Vertex; the plan's scaling pair needs another host.
- **API models change behind a name;** every output row logs the exact `model_id`.

## Adding a model

1. Add an entry under `models:` in `config.yaml` with its `provider`, `model`, auth (`api_key_env` or Vertex `location`), and any `extra_body` that turns thinking off.
2. Run one tiny call: section 3 of the notebook, or `python -m src.run --model <key> --limit-pairs 1`.
3. Run the smoke test (`--limit-pairs 30`) and check the notebook's diagnostics: no errors, `reasoning` 0, C3 tool calls near 100%.
4. If the provider needs a signature or other field on tool calls written by the harness (as Gemini 3 does), set `injected_tool_call_extra`.
