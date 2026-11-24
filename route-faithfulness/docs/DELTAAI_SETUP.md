# DeltaAI: getting access and running Llama 3.1

DeltaAI is where the team runs the plan's open-weights pair, Llama-3.1 8B and 70B, which Vertex AI no longer serves. Access goes through ACCESS on Dilek's project. This guide follows NCSA's DeltaAI docs as of 2026-11-23. **The scripts have not run on DeltaAI yet**, so the first person to log in should do step 3 and report what it prints.

| Step | Who | Costs allocation? |
|---|---|---|
| 1. Get an account | Each person, once | No |
| 2. Log in | Each person | No |
| 3. One-time setup | Each person, once | No (login node only) |
| 4. Run a model | One person per model | Yes (GPU job) |
| 5. Judge and analyze | Anyone with Vertex access | No DeltaAI time |

## 1. Get an account

You are added through ACCESS with your student email; NCSA then creates your DeltaAI login.

1. Check your student email (and spam) for a message from ACCESS about being added to a project. If it has an invitation link, use it.
2. Create an ACCESS account at https://operations.access-ci.org/identity/new-user with **your student email** (gmail and yahoo addresses are rejected; the email must match your university). If it offers your university as the identity provider, pick it. If you had an XSEDE account, that already is your ACCESS account.
3. If there was no invitation link, send your **ACCESS ID** to the PI (Dilek) or whoever manages the project. Members are added by ACCESS ID, and credits are exchanged for "NCSA DeltaAI" from the project's page (Allocations → Exchange). Exchanges can take up to a week to approve.
4. Find your **NCSA username**: https://allocations.access-ci.org/profile → bottom of the page → "Resource Provider Site Usernames". It may differ from your university ID.
5. Set your NCSA password: https://identity.ncsa.illinois.edu/reset (a code goes to your profile email). Enroll **NCSA Duo**, which is separate from your university's Duo: https://wiki.ncsa.illinois.edu/display/cybersec/Duo+at+NCSA. Manage your profile at https://identity.ncsa.illinois.edu/manage.
6. Test in a browser: https://gh-ondemand.delta.ncsa.illinois.edu (NCSA username, password, Duo). "Error – failed to map user" means NCSA has not finished your account; wait for their email. New accounts can take a few days.

## 2. Log in

```bash
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=keyboard-interactive NCSA_USERNAME@dtai-login.delta.ncsa.illinois.edu
```

- Expect `Password:` and then a Duo prompt (type `1` for a push). SSH keys are disabled on DeltaAI; if your laptop offers keys first, the server can drop you with "Too many authentication failures", which the two `-o` options avoid. Stop after two failures and check the password in the browser first: repeated failures can lock the account.
- No terminal? Use the browser shell: https://gh-ondemand.delta.ncsa.illinois.edu/pun/sys/shell/ssh/gh-login
- Long sessions: run `tmux` on a specific login node (`gh-login01` … `gh-login04.delta.ncsa.illinois.edu`) so you can reattach.
- To let a tool reuse your login without your password, open one shared connection: add `-fN -o ControlMaster=yes -o ControlPersist=10h -o ControlPath=~/.ssh/cm-dtai` to the command above; close it with `ssh -O exit -o ControlPath=~/.ssh/cm-dtai NCSA_USERNAME@dtai-login.delta.ncsa.illinois.edu`.

## 3. One-time setup (login node, free)

```bash
accounts                                              # your project, e.g. abcd-dtai-gh, and its balance in hours
cd /work/hdd/<project>/$USER                          # HOME is only 100 GB; work here
git clone https://github.com/sandeepstele/546.git     # use dhanushya08/546 once PR #1 is merged
cd 546/route-faithfulness
bash scripts/deltaai_setup.sh <project>
```

The setup script builds `.venv` (Python 3.12 from `python/miniforge3_pytorch/2.10.0`), prepares the data, writes `deltaai.env`, and prints which ways of running vLLM exist on the system. Then:

1. **Hugging Face access.** Llama 3.1 is gated: accept Meta's license at https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct (covers 70B), create a read token, and on DeltaAI run `source deltaai.env && .venv/bin/hf auth login`. Never put the token in the repo.
2. **Download the weights** to `/work` (the compute nodes may not reach the internet; the docs do not say):
   ```bash
   source deltaai.env
   .venv/bin/hf download meta-llama/Llama-3.1-8B-Instruct     # about 16 GB
   .venv/bin/hf download meta-llama/Llama-3.1-70B-Instruct    # about 141 GB; /work/hdd default quota is 1,000 GB
   ```
3. **vLLM.** DeltaAI's CPUs are ARM (aarch64), and the docs have no vLLM guide. Use what step 3 of the setup script found, in this order:
   - a `vllm` or `llmflux` module, or the vLLM README under `/sw/user/python/`;
   - NVIDIA's vLLM container, which is built for Grace Hopper: `apptainer pull $WORK/vllm.sif docker://nvcr.io/nvidia/vllm:<tag>` (tags: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/vllm/tags), then set `VLLM_SIF=$WORK/vllm.sif` in `deltaai.env`;
   - a pip wheel, if the script found one for aarch64.
4. **Test on one GPU for 30 minutes** before any long job (`ghx4-interactive` costs double, so use `ghx4`):
   ```bash
   source deltaai.env
   srun --account=$ACCOUNT --partition=ghx4 --nodes=1 --tasks=1 --cpus-per-task=16 --mem=100g --gpus-per-node=1 --time=00:30:00 --pty bash
   # on the compute node: start vLLM for 8B as in scripts/delta_serve_and_run.sbatch, then
   source .venv/bin/activate && python -m src.run --model llama31_8b_vllm --limit-pairs 3
   python -m src.peek --model llama31_8b_vllm --condition C3 --n 2
   ```
   Check that C3 shows `tool called` near 100% and the transcripts look right.

## 4. Run a model (GPU job, spends allocation)

From `route-faithfulness/`:

```bash
source deltaai.env
sbatch --account=$ACCOUNT scripts/delta_serve_and_run.sbatch llama8b
sbatch --account=$ACCOUNT --gpus-per-node=2 --cpus-per-task=32 --mem=200g --time=08:00:00 scripts/delta_serve_and_run.sbatch llama70b
squeue -u $USER                              # job state
tail -f logs/route-vllm-<jobid>.out          # progress
```

The job starts vLLM, waits for it, runs conditions C1, C2, T1, C3, C4, C5 on all 940 pairs, and stops. Rerunning resumes.

**Charging:** 1 SU = one GH200 (one H100 GPU, 72 cores, about 110 GB of CPU memory) for one hour, counted on what the job reserves, not what it uses. The job is charged the largest of: GPUs, memory ÷ 110 GB, cores ÷ 72. So 1 GPU with 100 GB = 1 SU per hour; 1 GPU with 220 GB = 2 SUs per hour. `ghx4` has charge factor 1 and a 48-hour limit; `ghx4-interactive` has factor 2, a 2-hour limit and one job per user. A full node for an hour costs 4 SUs. Rough guess, not yet measured: 8B uses about 1 GPU-hour for the full run; 70B on 2 GPUs a few hours, so under 10 SUs. Check the balance with `accounts`; a job stuck with `QOSGrpBillingMinutes` means the project is out of hours.

## 5. Judge and analyze

The judge runs on Vertex AI, so judge on a laptop with gcloud access:

```bash
# on your laptop, from route-faithfulness/
scp -r NCSA_USERNAME@dtai-login.delta.ncsa.illinois.edu:/work/hdd/<project>/<user>/546/route-faithfulness/outputs/raw/llama31_8b_vllm outputs/raw/
python -m src.judge --model llama31_8b_vllm
python -m src.analyze
```

For large transfers NCSA recommends Globus. Share the finished outputs as a dated folder under `runs/` (see `runs/2026-11-23/README.md`).

## DeltaAI facts in one place

| Item | Value |
|---|---|
| Nodes | 152 nodes × 4 GH200 (H100 96 GB GPU + 72-core Grace ARM CPU, 120 GB) each |
| Login | `dtai-login.delta.ncsa.illinois.edu`; NCSA password + Duo; no SSH keys; no GPUs on login nodes |
| Web | https://gh-ondemand.delta.ncsa.illinois.edu (JupyterLab with conda kernels, shell) |
| Storage | HOME `/u/$USER` 100 GB · PROJECTS `/projects/<project>/$USER` 500 GB · WORK `/work/hdd/<project>/$USER` and `/work/nvme/<project>/$USER` 1,000 GB each · `/tmp` 3.9 TB per node, wiped after each job · no `/scratch` |
| Partitions | `ghx4`: 48 h max, factor 1 · `ghx4-interactive`: 2 h max, factor 2, one job per user |
| Job defaults | 30 minutes, 1,000 MB per core; set `--time` and `--mem` |
| Python | `module load python/miniforge3_pytorch/2.10.0` (default; Python 3.12) · 2.11.0 and 2.12.0 also exist · `pip install --user` does not work, use a venv |
| Containers | Apptainer (`apptainer exec --nv`); NGC images in `/sw/user/NGC_containers/`; set `APPTAINER_CACHEDIR` to `/work` |
| Balance | `accounts` (hours left per project) |
| Help | http://help.ncsa.illinois.edu, or help@ncsa.illinois.edu with "DeltaAI" at the start of the subject; ACCESS issues: https://support.access-ci.org/open-a-ticket |

Not stated in the docs, to check on first login: whether compute nodes reach the internet, how vLLM is meant to run on ARM, and the exact project name. Docs: https://docs.ncsa.illinois.edu/systems/deltaai/en/latest/ (user-guide pages: accounts, login, running-jobs, job-accounting, data-mgmt, software, containers, ood).
