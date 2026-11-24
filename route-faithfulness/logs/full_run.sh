#!/usr/bin/env bash
# Full run: both models in parallel, then judge each, then analyze. Safe to rerun (resumes).
cd "$(dirname "$0")/.." && source .venv/bin/activate
CONDS="C1 C2 T1 C3 C4 C5"
for m in claude_sonnet46 gemini35_flash; do
  ( python -m src.run --model $m --conditions $CONDS --concurrency 16 && python -m src.judge --model $m --conditions $CONDS ) > logs/$m.log 2>&1 &
done
wait
python -m src.analyze --models claude_sonnet46 gemini35_flash > logs/analyze.log 2>&1
echo "FULL RUN FINISHED $(date)" >> logs/analyze.log
