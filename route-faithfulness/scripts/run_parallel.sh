#!/usr/bin/env bash
# Full run for several models in parallel (different providers do not share rate limits),
# then judge each model and analyze. Resumable: rerun the same command after an interruption.
#
#   bash scripts/run_parallel.sh claude_sonnet46 gemini35_flash
#   CONDS="C1 C2 T1 C3" CONCURRENCY=8 bash scripts/run_parallel.sh claude_sonnet46
#
# On a Mac, keep it awake for a long run:  caffeinate -i bash scripts/run_parallel.sh ...
# Per-model progress: logs/<model>.log
set -uo pipefail
cd "$(dirname "$0")/.."
[ $# -ge 1 ] || { echo "usage: scripts/run_parallel.sh <model key> [<model key> ...]"; exit 1; }
CONDS="${CONDS:-C1 C2 T1 C3 C4 C5}"
CONCURRENCY="${CONCURRENCY:-16}"
mkdir -p logs
for m in "$@"; do
  ( python -m src.run --model "$m" --conditions $CONDS --concurrency "$CONCURRENCY" \
      && python -m src.judge --model "$m" --conditions $CONDS ) > "logs/$m.log" 2>&1 &
  echo "started $m (log: logs/$m.log)"
done
wait
python -m src.analyze --models "$@"
echo "done: results/summary.md"
