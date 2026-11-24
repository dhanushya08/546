#!/usr/bin/env bash
# One-time setup on a DeltaAI LOGIN node. Free: no GPU, no job, nothing charged. Safe to rerun.
#
#   bash scripts/deltaai_setup.sh                 # lists your projects (`accounts`) and stops
#   bash scripts/deltaai_setup.sh abcd-dtai-gh    # your project name from `accounts`
#
# It builds the Python environment, prepares the FaithConflict data, writes deltaai.env
# (project, work folder, caches), and reports which ways of running vLLM exist on this system.
# See docs/DELTAAI_SETUP.md.
set -uo pipefail
cd "$(dirname "$0")/.."

ACCOUNT="${1:-}"
if [ -z "$ACCOUNT" ]; then
  accounts || true
  echo
  echo "Run again with your project name from the Account column above, e.g.:"
  echo "  bash scripts/deltaai_setup.sh abcd-dtai-gh"
  exit 1
fi

WORK="/work/hdd/$ACCOUNT/$USER"          # big storage for weights and caches (HOME is only 100 GB)
PYMOD="python/miniforge3_pytorch/2.10.0" # docs: the default Python module, Python 3.12
mkdir -p "$WORK/hf_cache" "$WORK/apptainer_cache" logs

echo "== Python environment (.venv) =="
module load "$PYMOD"
[ -x .venv/bin/python ] || python -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt "huggingface_hub[cli]" && echo "packages installed"

# Keys file the harness reads. vLLM needs no real key. Never commit .env.
touch .env
grep -q '^VLLM_API_KEY=' .env || echo 'VLLM_API_KEY=EMPTY' >> .env

cat > deltaai.env <<EOF
# Written by scripts/deltaai_setup.sh; read by scripts/delta_serve_and_run.sbatch. Not committed.
ACCOUNT=$ACCOUNT
WORK=$WORK
PYMOD=$PYMOD
export HF_HOME=$WORK/hf_cache
export APPTAINER_CACHEDIR=$WORK/apptainer_cache
# Set after getting a vLLM container (docs/DELTAAI_SETUP.md step 3); leave empty to use a vllm on PATH.
VLLM_SIF=${VLLM_SIF:-}
EOF
echo "wrote deltaai.env"

echo "== Data =="
.venv/bin/python -m src.data --prepare 2>&1 | grep -E "Wrote|Pairs per group" || echo "data prepare failed: run .venv/bin/python -m src.data --prepare to see why"

echo "== Ways to run vLLM on this system =="
echo "-- modules:"; (module -t spider vllm 2>&1; module -t avail llmflux 2>&1) | grep -iv "^$" | head -6
echo "-- NGC containers:"; ls /sw/user/NGC_containers/ /sw/external/NGC/ 2>/dev/null | grep -iE "vllm|pytorch_2[56]" | tail -6
echo "-- vLLM notes in the Python recipes:"; find /sw/user/python -maxdepth 3 -iname "*vllm*" 2>/dev/null | head -5
echo "-- vllm wheel for this CPU (aarch64) on PyPI:"
.venv/bin/pip download vllm --no-deps --only-binary=:all: -d /tmp/vllm-probe-$USER -q 2>/dev/null \
  && ls /tmp/vllm-probe-$USER && rm -rf /tmp/vllm-probe-$USER || echo "no binary wheel found"

echo "== Internet from the login node =="
curl -s -o /dev/null -w "huggingface.co: HTTP %{http_code}\n" --max-time 10 https://huggingface.co || echo "huggingface.co: unreachable"

echo
echo "Next: docs/DELTAAI_SETUP.md step 3 (Hugging Face login, model weights, vLLM)."
