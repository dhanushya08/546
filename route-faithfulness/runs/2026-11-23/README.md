# Run snapshot, 2026-11-23

Full run of the ladder on all 940 FaithConflict pairs (1,880 documents per condition), temperature 0, thinking off. **Complete**: every document answered and judged.

| Config key | Model | Route |
|---|---|---|
| `claude_sonnet46` | `claude-sonnet-4-6` | Claude API |
| `gemini35_flash` | `google/gemini-3.5-flash` | Vertex AI |
| judge | `openai/gpt-oss-120b-maas` | Vertex AI |

Conditions: C1 Direct, C2 Reshaped, T1 Tool-injected, C3 Tool, C4 RAG-oracle, C5 RAG-BM25 (see [../../docs/STUDY_DESIGN.md](../../docs/STUDY_DESIGN.md)). Settings: `config.yaml` at the commit that added this folder.

## Headline results (unvalidated judge)

Faithful rate on **opposing** documents (B1 or B2), percent. Full tables, CIs and figures: [results/summary.md](results/summary.md).

| Model | C1 Direct | C2 Reshaped | T1 Tool-injected | C3 Tool | C4 RAG-oracle | C5 RAG-BM25 |
|---|---|---|---|---|---|---|
| Claude Sonnet 4.6 | 33.3 | 17.8 | 27.8 | 27.9 | 15.9 | 27.8 |
| Gemini 3.5 Flash | 42.7 | 21.9 | 34.0 | 33.7 | 26.0 | 39.4 |

Ladder steps on opposing documents (McNemar, Holm-corrected):

| Step | What changes | Claude | Gemini |
|---|---|---|---|
| C1 → C2 | Wording and order | −15.5 pts, p < 1e-20 | −20.8 pts, p < 1e-30 |
| C2 → T1 | Channel (tool message) | +10.0 pts, p < 1e-12 | +12.5 pts, p < 1e-18 |
| T1 → C3 | Agency (model makes the call) | +0.1 pts, p = 1 | −1.5 pts, p = 0.28 |

How to read it:

- Direct (C1) to tool (C3) loses 5.4 points for Claude and 9.0 for Gemini, smaller than the GPT-4o pilot's 41. The loss comes from rewording the prompt (C1 → C2); delivering the document through a tool then recovers part of it, and who makes the call does not matter.
- Silent inversions (B8) are rare: 0.4-2.8% of opposing answers for Claude, under 1% for Gemini (pilot: 72 of 386).
- Most unfaithful labels are `O` (omission): the answer relays "the evidence is robust" without restating the conclusion. Counting those as faithful (the lenient bracket, `F_opp_lenient`) gives 82-86% for Claude and 96-99% for Gemini in every condition, and the route differences mostly vanish. **Validate the judge on hand labels before using any of these numbers** (TEAM_GUIDE task 2).
- Alignment specificity (code's definition) is negative for every route: safety documents start near the floor (Claude 8.5%, Gemini 17.1% faithful at C1), so they have little room to drop.
- Claude refuses (B7) on 12% of opposing documents at C1 and 6% at C3.

## Known issues

- Gemini C3: 69 empty answers from malformed tool calls, clustered on safety documents (25 of 386 safety-opposing); T1: 22 empty answers. Unlabeled, so they drop out of the rates (TEAM_GUIDE task 3).
- Claude: 8 API-level refusals (`stop_reason: refusal`, empty text), all on capability math items (4 in C1, 4 in C5). Also unlabeled; arguably B7.
- 3 Gemini answers stayed unparseable for the judge after retries.
- Gemini is not deterministic at temperature 0; 2 Gemini T1 answers showed reasoning tokens.

## Files

| Path | What |
|---|---|
| `outputs/raw/<model>/<condition>.jsonl.gz` | One row per document: full transcript (`messages`), answer, tool calls, token usage, exact `model_id` |
| `outputs/judged/<model>/<condition>.jsonl.gz` | The same rows without transcripts, plus the judge's label (`code`), rationale and route event |
| `results/` | `summary.md`, per-model CSVs and figures from the full run |
| `smoke_results/` | The same for the 30-pair smoke test (60 documents per condition) |

## Restore and analyze

From `route-faithfulness/` (this overwrites your own `outputs/` for these two models):

```bash
mkdir -p outputs && cp -R runs/2026-11-23/outputs/. outputs/
gunzip -f outputs/*/*/*.jsonl.gz
python -m src.analyze --models claude_sonnet46 gemini35_flash      # rebuilds results/
python -m src.peek --model gemini35_flash --condition C3 --polarity opposing --n 3
```

## Cost (measured from logged token usage, list prices)

| Model | Price per 1M tokens (in / out) | Tokens (in / out) | Cost incl. smoke test |
|---|---|---|---|
| Claude Sonnet 4.6 | $3 / $15 | 10.18M / 2.59M | $69.41 |
| Gemini 3.5 Flash | $1.50 / $9 | 6.47M / 1.03M | $18.99 |
| gpt-oss-120b judge | $0.09 / $0.36 | not logged | about $8, estimated |

Claude costs about 3.5x Gemini: higher prices, answers 2-3x longer, and about 500 extra input tokens per call when tools are sent. Wall time: about 1.5 hours for both models plus judging, run in parallel at concurrency 16 (Gemini's answers alone took 33 minutes).
