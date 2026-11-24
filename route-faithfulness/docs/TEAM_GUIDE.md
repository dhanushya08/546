# Team guide: Does the Route Matter?

Start here. This page says where the project stands, what is left, and where everything lives.
Last updated 2026-11-23.

| Doc | What it holds |
|---|---|
| [TEAM_GUIDE.md](TEAM_GUIDE.md) (this page) | Status, open tasks, decisions, where things live |
| [STUDY_DESIGN.md](STUDY_DESIGN.md) | The plan: ladder, taxonomy, metrics, controls, and how each maps to the code |
| [MODELS_AND_PROVIDERS.md](MODELS_AND_PROVIDERS.md) | Which models run where, provider quirks, measured costs, caveats for the paper |
| [research/vertex_claude_setup.md](research/vertex_claude_setup.md) | Research report on Claude API + Vertex AI (sources for the provider choices) |
| [../README.md](../README.md) | How to install and run every step |

## Status

Both models finished the 30-pair smoke test, and the full 940-pair run is under way. Gemini 3.5 Flash has answered all 11,280 documents; Claude Sonnet 4.6 is past its halfway point.

| Piece | State | Detail |
|---|---|---|
| Claude API + Vertex AI support, T1 rung, notebook | In review | [PR #1](https://github.com/dhanushya08/546/pull/1) |
| Smoke test, 30 pairs, Claude Sonnet 4.6 + Gemini 3.5 Flash | Done | 0 API errors; tools called 100% in C3 |
| Full run, Gemini 3.5 Flash (C1, C2, T1, C3, C4, C5) | Answers done, judging | 11,280 documents, $18.99 |
| Full run, Claude Sonnet 4.6 (same conditions) | Running | about $70 when done |
| Claude on Vertex AI | Blocked | Project quota is 0; needs a quota request |
| Llama 3.1 8B / 70B | Blocked on Vertex | No longer served there; see [MODELS_AND_PROVIDERS.md](MODELS_AND_PROVIDERS.md) |
| Judge validation (kappa) | Not started | Needed before trusting any number |

Run outputs (`outputs/`, `results/`) are not in git (`.gitignore`). Until a shared bucket exists, ask whoever ran a model for a zip of `outputs/raw/<model>/` and `outputs/judged/<model>/`; `python -m src.analyze` rebuilds `results/` from them.

## Open tasks

Pick a task, put your name in the Owner column in a PR, and link your PR in Notes. Ordered by what blocks the paper most.

| # | Task | Why | Owner | Notes |
|---|---|---|---|---|
| 1 | Review and merge PR #1 | Everything below builds on it | | |
| 2 | Validate the judge: ~150 hand labels, Cohen's kappa | The smoke test labeled many answers `O` (omission), even on confirming documents. If the judge is wrong there, every rate is wrong. | | `python -m src.validate_judge --export-sample 150 --models claude_sonnet46 gemini35_flash`, label blind, then `--human-csv` (README step 5) |
| 3 | Decide how empty answers count | Gemini made a malformed tool call on 69 of 1,880 C3 documents, 42 of them safety. These are excluded from rates now, which can make C3 look more faithful on safety than it is. | | Options: exclude and report the rate (now), count as unfaithful, or count as refusal (B7). See STUDY_DESIGN.md "Open decisions" |
| 4 | Write up the plan | Paper sections 1-3 | | STUDY_DESIGN.md has the design in one place |
| 5 | Add T3: the three tool descriptions | Plan rung T3 (source trust). Today every tool run uses the "verbatim and unmodified" description, i.e. T3-trusted. | | Add `neutral` and `unverified` descriptions as new conditions; see STUDY_DESIGN.md |
| 6 | Add the quote probe | Separates override (read the claim, changed it) from reading failure | | A separate pass: ask for the conclusion sentence, then the answer |
| 7 | Add GPT-4o | Continuity with the pilot (70% to 29%) | | Needs `OPENAI_API_KEY`; config key `gpt4o` exists |
| 8 | Add an open-weights model | Plan's Llama-3.1 8B / 70B scaling pair | | Llama 3.1 via vLLM on Delta (README section 10), or Llama 4 Scout / Maverick on Vertex |
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
| Raw answers / judged answers | `outputs/raw/<model>/<condition>.jsonl`, `outputs/judged/<model>/<condition>.jsonl` (not in git) |
| Tables and figures | `results/summary.md`, `results/figures/` (rebuilt by `python -m src.analyze`) |

## How to pick up a task

1. Clone the repo, then follow README section 4 steps 0-1 (install, offline mock test). The mock test needs no keys.
2. Work on a branch, open a PR, and update the Owner and Notes columns above in the same PR.
3. Before spending on a full run, run the smoke test (`--limit-pairs 30`, or section 6 of the notebook). Its diagnostics table estimates the full-run cost from real token counts.
4. Rerunning any step resumes it. Deleting `outputs/raw/<model>/<condition>.jsonl` and the matching judged file starts a condition over.
