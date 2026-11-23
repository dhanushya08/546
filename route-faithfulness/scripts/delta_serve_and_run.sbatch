#!/bin/bash
# DeltaAI: serve an open model with vLLM on one GH200 GPU and run all conditions against it.
#
#   sbatch scripts/delta_serve_and_run.sbatch qwen
#   sbatch scripts/delta_serve_and_run.sbatch gemma
#
# Before the first run, edit the four values marked EDIT below (see README section 10).
#SBATCH --account=EDIT-dtai-gh          # EDIT: your project from the `accounts` command
#SBATCH --partition=ghx4
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=100g
#SBATCH --time=04:00:00
#SBATCH --job-name=route-vllm
#SBATCH --output=logs/%x-%j.out
set -euo pipefail

WHICH="${1:-qwen}"
SIF="EDIT/path/to/vllm.sif"                         # EDIT: the vLLM container (README section 10, step 3)
export HF_HOME="EDIT/your/project/or/work/dir/hf_cache"   # EDIT: big storage, not $HOME
PROJECT_DIR="EDIT/path/to/route-faithfulness"       # EDIT: where you unzipped the project

if [ "$WHICH" = "qwen" ]; then
  HF_MODEL="Qwen/Qwen3.5-9B"
  CONFIG_KEY="qwen35_9b_vllm"
  SERVE_ARGS="--enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3"
else
  HF_MODEL="google/gemma-4-12B-it"
  CONFIG_KEY="gemma4_12b_vllm"
  # Check the "vLLM" section of the Gemma 4 model card for the right tool-call parser name.
  SERVE_ARGS="--enable-auto-tool-choice --tool-call-parser EDIT_GEMMA_PARSER"
fi

cd "$PROJECT_DIR"
mkdir -p logs

echo "Starting vLLM for $HF_MODEL on $(hostname)"
apptainer exec --nv --bind /projects,/work "$SIF" \
  vllm serve "$HF_MODEL" --host 127.0.0.1 --port 8000 --max-model-len 16384 \
  --gpu-memory-utilization 0.85 $SERVE_ARGS > "logs/vllm-$WHICH-$SLURM_JOB_ID.log" 2>&1 &
VLLM_PID=$!

echo "Waiting for the server (loading weights takes a few minutes)..."
for i in $(seq 1 90); do
  if curl -s http://127.0.0.1:8000/v1/models > /dev/null; then echo "Server up."; break; fi
  if ! kill -0 $VLLM_PID 2>/dev/null; then echo "vLLM died. See logs/vllm-$WHICH-$SLURM_JOB_ID.log"; exit 1; fi
  sleep 10
done

source .venv/bin/activate
export VLLM_API_KEY=EMPTY
python -m src.run --model "$CONFIG_KEY" --concurrency 32

kill $VLLM_PID
echo "Done. Outputs in outputs/raw/$CONFIG_KEY/. Judge them with: python -m src.judge --model $CONFIG_KEY"
