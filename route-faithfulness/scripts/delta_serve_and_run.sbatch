#!/bin/bash
# DeltaAI: serve an open model with vLLM on GH200 GPUs and run every condition against it.
# Run scripts/deltaai_setup.sh once first; submit from route-faithfulness/ (see docs/DELTAAI_SETUP.md).
#
#   source deltaai.env
#   sbatch --account=$ACCOUNT scripts/delta_serve_and_run.sbatch llama8b
#   sbatch --account=$ACCOUNT --gpus-per-node=2 --cpus-per-task=32 --mem=200g --time=08:00:00 \
#          scripts/delta_serve_and_run.sbatch llama70b
#
# Charging: 1 SU = one GH200 for one hour, counted on what the job RESERVES: the larger of GPUs,
# memory / 110 GB and cores / 72. Keep --mem at or under 110g per GPU so memory does not add SUs.
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

WHICH="${1:-llama8b}"
cd "${SLURM_SUBMIT_DIR:-$(pwd)}"
[ -f deltaai.env ] || { echo "deltaai.env missing: run scripts/deltaai_setup.sh first"; exit 1; }
source deltaai.env
NGPU="${SLURM_GPUS_ON_NODE:-1}"

case "$WHICH" in
  llama8b)
    HF_MODEL="meta-llama/Llama-3.1-8B-Instruct";  CONFIG_KEY="llama31_8b_vllm"
    SERVE_ARGS="--enable-auto-tool-choice --tool-call-parser llama3_json --max-model-len 16384" ;;
  llama70b)
    HF_MODEL="meta-llama/Llama-3.1-70B-Instruct"; CONFIG_KEY="llama31_70b_vllm"
    SERVE_ARGS="--enable-auto-tool-choice --tool-call-parser llama3_json --max-model-len 8192" ;;
  qwen)
    HF_MODEL="Qwen/Qwen3.5-9B"; CONFIG_KEY="qwen35_9b_vllm"
    SERVE_ARGS="--enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3" ;;
  gemma)
    HF_MODEL="google/gemma-4-12B-it"; CONFIG_KEY="gemma4_12b_vllm"
    # Check the "vLLM" section of the Gemma 4 model card for the right tool-call parser name.
    SERVE_ARGS="--enable-auto-tool-choice --tool-call-parser EDIT_GEMMA_PARSER" ;;
  *) echo "unknown model '$WHICH' (llama8b, llama70b, qwen, gemma)"; exit 1 ;;
esac

# vLLM from the container in deltaai.env, else a `vllm` already on PATH.
if [ -n "${VLLM_SIF:-}" ]; then RUN=(apptainer exec --nv --bind /projects,/work,/tmp "$VLLM_SIF"); else RUN=(); fi

mkdir -p logs
echo "Starting vLLM for $HF_MODEL on $(hostname) with $NGPU GPU(s)"
"${RUN[@]}" vllm serve "$HF_MODEL" --host 127.0.0.1 --port 8000 --tensor-parallel-size "$NGPU" \
  --gpu-memory-utilization 0.90 $SERVE_ARGS > "logs/vllm-$WHICH-$SLURM_JOB_ID.log" 2>&1 &
VLLM_PID=$!

echo "Waiting for the server (70B takes several minutes to load)..."
for i in $(seq 1 180); do
  if curl -s http://127.0.0.1:8000/v1/models > /dev/null; then echo "Server up after $((i * 10)) s."; break; fi
  if ! kill -0 $VLLM_PID 2>/dev/null; then echo "vLLM died. See logs/vllm-$WHICH-$SLURM_JOB_ID.log"; exit 1; fi
  sleep 10
done

source .venv/bin/activate
python -m src.run --model "$CONFIG_KEY" --concurrency 32

kill $VLLM_PID
echo "Done. Outputs in outputs/raw/$CONFIG_KEY/. Copy them to a machine with Vertex access to judge"
echo "(docs/DELTAAI_SETUP.md step 5), or run: python -m src.judge --model $CONFIG_KEY"
