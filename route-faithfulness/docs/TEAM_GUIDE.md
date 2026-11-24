# Team guide: Does the Route Matter?

Start here. This page says where the project stands, what is left, and where everything lives.
Last updated 2026-11-23.

| Doc | What it holds |
|---|---|
| [TEAM_GUIDE.md](TEAM_GUIDE.md) (this page) | Status, open tasks, decisions, where things live |
| [STUDY_DESIGN.md](STUDY_DESIGN.md) | The plan: ladder, taxonomy, metrics, controls, and how each maps to the code |
| [MODELS_AND_PROVIDERS.md](MODELS_AND_PROVIDERS.md) | Which models run where, provider quirks, measured costs, caveats for the paper |
| [DELTAAI_SETUP.md](DELTAAI_SETUP.md) | DeltaAI: getting an account through ACCESS, logging in, running Llama 3.1 8B / 70B with vLLM |
| [research/vertex_claude_setup.md](research/vertex_claude_setup.md) | Research report on Claude API + Vertex AI (sources for the provider choices); raw notes in [research/notes/](research/notes/) |
| [../runs/2026-11-23/README.md](../runs/2026-11-23/README.md) | The full run's outputs: what is in the snapshot, how to restore and analyze it, costs |
| [../README.md](../README.md) | How to install and run every step |

## Status

The full 940-pair run is done for Claude Sonnet 4.6 and Gemini 3.5 Flash: every document answered and judged, results in [`runs/2026-11-23/`](../runs/2026-11-23/README.md). The first reading is below; none of it holds until the judge is validated (task 2).

| Piece | State | Detail |
|---|---|---|
| Claude API + Vertex AI support, T1 rung, notebook | In review | [PR #1](https://github.com/dhanushya08/546/pull/1) |
| Smoke test, 30 pairs, Claude Sonnet 4.6 + Gemini 3.5 Flash | Done | 0 API errors; tools called 100% in C3 |
| Full run, Gemini 3.5 Flash (C1, C2, T1, C3, C4, C5) | Done | 11,280 documents, $18.99 |
| Full run, Claude Sonnet 4.6 (same conditions) | Done | 11,280 documents, $69.41 |
| DeltaAI for Llama 3.1 | Scripts ready, untested | Waiting on DeltaAI accounts ([DELTAAI_SETUP.md](DELTAAI_SETUP.md)) |
| Claude on Vertex AI | Blocked | Project quota is 0; needs a quota request |
| Llama 3.1 8B / 70B | Blocked on Vertex | No longer served there; see [MODELS_AND_PROVIDERS.md](MODELS_AND_PROVIDERS.md) |
| Judge validation (kappa) | Not started | Needed before trusting any number |

**First reading of the full run** (faithful rate on opposing documents, %, strict judge):

| Model | C1 Direct | C2 Reshaped | T1 Tool-injected | C3 Tool | C4 RAG-oracle | C5 RAG-BM25 |
|---|---|---|---|---|---|---|
| Claude Sonnet 4.6 | 33.3 | 17.8 | 27.8 | 27.9 | 15.9 | 27.8 |
| Gemini 3.5 Flash | 42.7 | 21.9 | 34.0 | 33.7 | 26.0 | 39.4 |

- The drop from direct to tool is 5 to 9 points, not the pilot's 41, and it comes from rewording the prompt (C1 → C2). The tool channel then recovers part of it (C2 → T1, +10 to +12 points), and agency (T1 → C3) changes nothing.
- Silent inversions are rare (under 3%). Most failures are `O`: the answer relays "the evidence is robust" without restating the conclusion. With those counted as faithful (lenient), every condition is 82-86% (Claude) or 96-99% (Gemini) and the route effect mostly disappears. Whether `O` is a real failure on these vague template documents is the question the judge validation has to settle.
- Safety documents start near the floor (Claude 8.5%, Gemini 17.1% at C1), so alignment specificity comes out negative.

The run's outputs are in git twice: ready to use in `outputs/`, `results/`, `logs/` and `data/`, and as a compressed, frozen copy in [`runs/2026-11-23/`](../runs/2026-11-23/README.md). Clone the repo and `python -m src.analyze` or `python -m src.peek` work straight away. Commit new runs' outputs the same way; the mock test only writes to `outputs_mock/` and `results_mock/`, which stay out of git.

## Open tasks

Pick a task, put your name in the Owner column in a PR, and link your PR in Notes. Ordered by what blocks the paper most.

| # | Task | Why | Owner | Notes |
|---|---|---|---|---|
| 1 | Review and merge PR #1 | Everything below builds on it | | |
| 2 | Validate the judge: ~150 hand labels, Cohen's kappa | The smoke test labeled many answers `O` (omission), even on confirming documents. If the judge is wrong there, every rate is wrong. | | `python -m src.validate_judge --export-sample 150 --models claude_sonnet46 gemini35_flash`, label blind, then `--human-csv` (README step 5) |
| 3 | Decide how empty answers count | Gemini made a malformed tool call on 69 of 1,880 C3 documents, 42 of them safety; Claude returned 8 API-level refusals (empty text) on capability math items. These are excluded from rates now, which can make C3 look more faithful on safety than it is. | | Options: exclude and report the rate (now), count as unfaithful, or count as refusal (B7). See STUDY_DESIGN.md "Open decisions" |
| 4 | Write up the plan | Paper sections 1-3 | | STUDY_DESIGN.md has the design in one place |
| 5 | Add T3: the three tool descriptions | Plan rung T3 (source trust). Today every tool run uses the "verbatim and unmodified" description, i.e. T3-trusted. | | Add `neutral` and `unverified` descriptions as new conditions; see STUDY_DESIGN.md |
| 6 | Add the quote probe | Separates override (read the claim, changed it) from reading failure | | A separate pass: ask for the conclusion sentence, then the answer |
| 7 | Add GPT-4o | Continuity with the pilot (70% to 29%) | | Needs `OPENAI_API_KEY`; config key `gpt4o` exists |
| 8 | Run Llama-3.1 8B and 70B on DeltaAI | Plan's open-weights scaling pair | | Config keys and scripts are ready; follow [DELTAAI_SETUP.md](DELTAAI_SETUP.md). First: accounts via ACCESS on Dilek's project, then step 3 and report what it prints |
| 9 | Check Gemini's nondeterminism | Two identical T1 requests gave different answers at temperature 0 | | Rerun ~100 documents per condition; report agreement |
| 10 | Reconcile metric definitions with the plan | Alignment specificity and bootstrap count differ between plan and code | | STUDY_DESIGN.md "Plan vs code" |
| 11 | Claude on Vertex AI (optional) | Only if Claude must be billed through Google | | Enable Sonnet 4.6 in Model Garden, request `global_online_prediction_requests_per_base_model` quota |

## Decisions the team still owes

- How empty answers and malformed tool calls count (task 3).
- Which open-weights model, if any, goes in the paper (task 8).
- Whether R2 (competing evidence) and A1 (agent, C6) are in scope or future work. The plan asks this; C6 is coded but has not been run on real models.
- Whether to keep C5 (BM25 retrieval). It is in the code but not on the plan's ladder.
- Judge model for the final numbers: gpt-oss-120b on Vertex now; the README suggests gpt-4o-mini.

## Where things live

| What | Where |
|---|---|
| Code | `src/` (one module per step; README section 8 lists them) |
| Every setting: models, prompts, conditions, judge | `config.yaml` |
| Setup + smoke test + full run, locally or on Vertex AI | `notebooks/vertex_setup_and_run.ipynb` |
| API keys | `.env`, git-ignored; template in `.env.example`. Never commit keys or paste them into the notebook |
| Raw answers / judged answers | `outputs/raw/<model>/<condition>.jsonl`, `outputs/judged/<model>/<condition>.jsonl` (in git) |
| Run logs | `logs/<model>.log`, `logs/analyze.log` (in git) |
| Prepared dataset | `data/faithconflict.jsonl` (in git; CC BY 4.0, see `data/README.md`) |
| Frozen run snapshots | `runs/<date>/` (in git; gzipped) |
| Launch several models in parallel | `scripts/run_parallel.sh <model> <model> ...` |
| Tables and figures | `results/summary.md`, `results/figures/` (in git; rebuilt by `python -m src.analyze`) |

## How to pick up a task

1. Clone the repo, then follow README section 4 steps 0-1 (install, offline mock test). The mock test needs no keys.
2. Work on a branch, open a PR, and update the Owner and Notes columns above in the same PR.
3. Before spending on a full run, run the smoke test (`--limit-pairs 30`, or section 6 of the notebook). Its diagnostics table estimates the full-run cost from real token counts.
4. Rerunning any step resumes it. Deleting `outputs/raw/<model>/<condition>.jsonl` and the matching judged file starts a condition over.
