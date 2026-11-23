#!/usr/bin/env bash
# Run, judge and analyze one model end to end. Safe to rerun: every step resumes.
#   bash scripts/run_model.sh gpt4o
#   bash scripts/run_model.sh qwen35_9b
set -euo pipefail
cd "$(dirname "$0")/.."
MODEL="${1:?usage: scripts/run_model.sh <model key from config.yaml>}"
python -m src.run   --model "$MODEL"
python -m src.judge --model "$MODEL"
python -m src.analyze
