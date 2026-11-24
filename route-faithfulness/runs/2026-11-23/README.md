# Run snapshot, 2026-11-23

Full run of the ladder on all 940 FaithConflict pairs (1,880 documents per condition), temperature 0, thinking off.

| Config key | Model | Route |
|---|---|---|
| `claude_sonnet46` | `claude-sonnet-4-6` | Claude API |
| `gemini35_flash` | `google/gemini-3.5-flash` | Vertex AI |
| judge | `openai/gpt-oss-120b-maas` | Vertex AI |

Conditions: C1, C2, T1, C3, C4, C5 (see [../../docs/STUDY_DESIGN.md](../../docs/STUDY_DESIGN.md)). Settings: `config.yaml` at the commit that added this folder.

## State of this snapshot

**Partial: the run was still going when this was saved.** It is refreshed when answering and judging finish. Counts include the 30-pair smoke test.

| Documents (of 1,880 per condition) | C1 | C2 | T1 | C3 | C4 | C5 |
|---|---|---|---|---|---|---|
| `claude_sonnet46` answered | 1,880 | 1,880 | 1,880 | 1,880 | 386 | 60 |
| `claude_sonnet46` judged | 60 | 60 | 60 | 60 | 60 | 60 |
| `gemini35_flash` answered | 1,880 | 1,880 | 1,880 | 1,880 | 1,880 | 1,880 |
| `gemini35_flash` judged | 1,880 | 60 | 60 | 60 | 60 | 60 |

## Files

| Path | What |
|---|---|
| `outputs/raw/<model>/<condition>.jsonl.gz` | One row per document: full transcript (`messages`), answer, tool calls, token usage, exact `model_id`. Gzipped (about 10x smaller) |
| `outputs/judged/<model>/<condition>.jsonl` | The same rows without transcripts, plus the judge's label (`code`), rationale and route event |
| `smoke_results/` | `summary.md`, tables and figures from the 30-pair smoke test (60 documents per condition) |

## Restore and analyze

From `route-faithfulness/` (this overwrites your own `outputs/` for these two models):

```bash
mkdir -p outputs && cp -R runs/2026-11-23/outputs/. outputs/
gunzip -kf outputs/raw/*/*.jsonl.gz
python -m src.analyze --models claude_sonnet46 gemini35_flash      # writes results/
python -m src.peek --model gemini35_flash --condition C3 --polarity opposing --n 3
```

`src.analyze` needs only `outputs/judged/`; the raw transcripts are for `src.peek`, re-judging and judge validation.

## Cost (measured from logged token usage, list prices)

| Model | Smoke test | Full run |
|---|---|---|
| Claude Sonnet 4.6 ($3 / $15 per 1M tokens) | $2.24 | about $70 when done ($47.18 at 7,637 documents) |
| Gemini 3.5 Flash ($1.50 / $9 per 1M tokens) | $0.62 | $18.37 |

Claude costs about 3.5x Gemini: higher prices, answers 2-3x longer (184-287 vs 78-110 output tokens), and about 500 extra input tokens per call when tools are sent.

## Known issues in this run

- Gemini C3: 69 empty answers from malformed tool calls, clustered on safety documents (25 of 386 safety-opposing). They have no label and drop out of the faithful rates; see [../../docs/TEAM_GUIDE.md](../../docs/TEAM_GUIDE.md) task 3.
- Gemini T1: 22 empty answers; 2 answers still showed reasoning tokens.
- Gemini is not deterministic at temperature 0 (the same request gave two different answers).
