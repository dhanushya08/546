#!/usr/bin/env bash
# Full pipeline on fake data with a fake model. No API keys, about a minute.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf outputs_mock results data/mock_faithconflict.jsonl
python -m src.mock
python -m src.data --prepare --config config.mock.yaml
python -m src.run   --model gpt4o --mock --config config.mock.yaml --conditions C1 C2 T1 C3 C4 C5 C6
python -m src.judge --model gpt4o --mock --config config.mock.yaml
python -m src.analyze --config config.mock.yaml
echo
echo "Mock pipeline OK. Open results/summary.md and results/figures/ to see the output format."
echo "Delete results/ before the real analysis (or just rerun src.analyze; it overwrites)."
