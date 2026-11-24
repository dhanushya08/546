# Running a GitHub-hosted experiment notebook on Vertex AI (Colab Enterprise vs Workbench), November 2026

Research date: 2026-11-23. All Google docs below were fetched on that date. Most pages showed "Last updated 2026-11-10" to "2026-11-20". Older pages are flagged inline.

**Naming change (affects every doc link and console label).** Google renamed Vertex AI to **"Gemini Enterprise Agent Platform"** at Cloud Next on 2026-04-22 ([Campus Technology, 2026-05-04](https://campustechnology.com/articles/2026/05/04/google-intros-new-gemini-enterprise-agent-platform.aspx); [Wikipedia](https://en.wikipedia.org/wiki/Gemini_Enterprise_Agent_Platform)). Docs now live under `docs.cloud.google.com/gemini-enterprise-agent-platform/...`, and old `cloud.google.com/vertex-ai/docs/...` URLs redirect there (seen while fetching). The console and docs now say "Agent Platform Workbench", "Agent Platform User", and "Create Agent Platform runtime". Role IDs and API names have not changed: `roles/aiplatform.user`, `aiplatform.googleapis.com`, `notebooks.googleapis.com` ([Use partner models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/use-partner-models)). Colab Enterprise docs stay at `docs.cloud.google.com/colab/docs/...`.

## Q1. Colab Enterprise vs Workbench for a CPU-only, multi-hour, network-bound job: idle shutdown, runtime templates, machine type, $/hour, regions

### Takeaway
Both products default to a 180-minute idle shutdown, and both can turn it off or raise it to 1440 minutes. Both bill the same E2 rates: about $0.08/h for e2-standard-2 and $0.16/h for e2-standard-4 in us-central1, before disk.

- **Colab Enterprise** is the better fit for "open a notebook and run it headless". It has runtime templates and one-off notebook executions (default timeout 24h) that do not depend on a browser. It also passes your own user credentials to ADC with no service-account setup.
- **Workbench** is the better fit when you want a persistent VM with a terminal, git, and a long-lived data disk. Its idle timer ignores CPU usage, so a background `nohup` job needs idle shutdown turned off.

### Cited Findings
**Colab Enterprise: idle shutdown**
- Runtimes shut down after **180 minutes** of inactivity by default. The console accepts 10–1440 minutes. gcloud accepts `10m`–`24h`, and `0s` turns idle shutdown off. [Colab idle shutdown](https://docs.cloud.google.com/colab/docs/idle-shutdown)
- You can only set idle shutdown when you create a runtime template, and the template can't be changed afterwards. To change it, create a new template and a new runtime from it. [Colab idle shutdown](https://docs.cloud.google.com/colab/docs/idle-shutdown)
- Console path: Colab Enterprise → **Runtime templates** → **New template** → **Configure compute** → **Idle shutdown**. There you can clear "Enable idle shutdown" or change "Time of inactivity before shutdown (Minutes)". [Colab idle shutdown](https://docs.cloud.google.com/colab/docs/idle-shutdown)
- Shutdown requires "no kernel activity for the specified time period". A runtime shuts down only when it "isn't connected to a notebook". [Colab idle shutdown](https://docs.cloud.google.com/colab/docs/idle-shutdown)

**Colab Enterprise: runtime template defaults** (`gcloud colab runtime-templates create`)
- `--machine-type` default is **"e2-standard-4"**.
- `--disk-size-gb` default is 100 (range 10–65536). `--disk-type` is one of PD_STANDARD, PD_SSD, PD_BALANCED, PD_EXTREME, HYPERDISK_BALANCED.
- `--idle-shutdown-timeout` default is "3h".
- `--enable-euc` (end-user credentials) is "Enabled by default". Use `--no-enable-euc` to turn it off.
- `--no-enable-internet-access` exists, which implies internet access is on by default.
- Source: [gcloud colab runtime-templates create](https://docs.cloud.google.com/sdk/gcloud/reference/colab/runtime-templates/create). Page last updated 2026-06-23; the flags may have changed since.

**Colab Enterprise: other runtime facts**
- Template console sections are Runtime basics, Configure compute, Environment, and Networking and security. The Environment default is "Latest". Networking and security has "Enable public internet access" and "Enable end-user credentials" toggles. [Create a runtime template](https://docs.cloud.google.com/colab/docs/create-runtime-template)
- Since 2026-11-09, Python 3.13 is the "latest" version. Templates set to "latest", including default runtime templates, now create Python 3.13 runtimes. [Colab release notes](https://docs.cloud.google.com/colab/docs/release-notes)
- Since 2026-09-28, the console can set an existing runtime template as the project/region **default runtime template**. [Colab release notes](https://docs.cloud.google.com/colab/docs/release-notes)
- Post-startup scripts are GA (2025-12-17). They can install packages after the runtime boots. [Colab release notes](https://docs.cloud.google.com/colab/docs/release-notes)
- Creating runtimes requires `roles/aiplatform.colabEnterpriseAdmin`. The runtime must be in the same region as the notebook. CLI: `gcloud colab runtimes create --display-name=... --runtime-template=TEMPLATE_ID --project=... --region=...`. [Create a runtime](https://docs.cloud.google.com/colab/docs/create-runtime). Page last updated 2026-06-18.

**Workbench: idle shutdown**
- Enabled by default with a 180-minute period. The console accepts 10–1440 minutes. [Workbench idle shutdown](https://docs.cloud.google.com/vertex-ai/docs/workbench/instances/idle-shutdown)
- What counts as activity: the instance shuts down after a period with no kernel activity. **Running a cell or new notebook output resets the timer. CPU usage does not reset it. Leaving JupyterLab open without interacting does not prevent shutdown.** [Workbench idle shutdown](https://docs.cloud.google.com/vertex-ai/docs/workbench/instances/idle-shutdown)
- The monitored endpoints include `127.0.0.1:8080/api/terminals`, `/api/sessions` and `/api/kernels`. [Workbench idle shutdown](https://docs.cloud.google.com/vertex-ai/docs/workbench/instances/idle-shutdown)
- Unlike Colab, the setting can be changed after creation. Console path: Instances → instance name → **Software and security** tab → "Enable Idle Shutdown" / "Time of inactivity before shutdown (Minutes)" → Submit. [Workbench idle shutdown](https://docs.cloud.google.com/vertex-ai/docs/workbench/instances/idle-shutdown)
- gcloud uses the `idle-timeout-seconds` metadata key. Examples from the doc: `gcloud workbench instances create INSTANCE_NAME --metadata=idle-timeout-seconds=86400` and `gcloud workbench instances update INSTANCE_NAME --metadata=idle-timeout-seconds=43200`. An empty value (`--metadata=idle-timeout-seconds=`) turns it off. Guest attributes must be enabled, which is the default. [Workbench idle shutdown](https://docs.cloud.google.com/vertex-ai/docs/workbench/instances/idle-shutdown)
- While the instance is shut down there are no CPU or GPU charges, but disk storage charges continue. [Workbench idle shutdown](https://docs.cloud.google.com/vertex-ai/docs/workbench/instances/idle-shutdown)

**Workbench: instance defaults**
- `gcloud workbench instances create`: boot disk and data disk each default to 100 GB of PD_STANDARD. If no service account is given, the Compute Engine default service account is used. The doc example uses `--machine-type=n1-standard-4 --location=us-central1-b`. The reference does not state a default machine type. [gcloud workbench instances create](https://docs.cloud.google.com/sdk/gcloud/reference/workbench/instances/create). Page last updated 2026-10-27.
- Creating an instance requires `roles/notebooks.admin`. The console path is Instances → **Create new**. Advanced options include JupyterLab version, post-startup script, and machine type (with monthly cost estimates), plus idle shutdown in the Software and security section. [Workbench create](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/create); [Workbench quickstart](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/create-console-quickstart)
- Since 2026-11-10 (Preview), new Workbench instances on Debian 12 images (`workbench-instances-2603`) have the Antigravity CLI agent turned on by default. Turn it off with metadata `enable-antigravity=false`. [Workbench release notes](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/release-notes)

**Pricing**

Rates are from [Colab pricing](https://cloud.google.com/colab/pricing) and the "Workbench in Gemini platform" section of [Gemini platform pricing](https://cloud.google.com/vertex-ai/pricing), both downloaded 2026-11-23, in the default-rendered region. Iowa (us-central1) is the first region in each table's selector.

| Item | Rate (USD) | Notes |
|---|---|---|
| E2 vCPU (Colab Enterprise) | $0.026173908 per hour | Management fee $0.004362318 per hour |
| E2 memory (Colab Enterprise) | $0.003508236 per GiB-hour | Management fee $0.000584706 per GiB-hour |
| Colab disk: SSD | $0.000279452 per GiB-hour | |
| Colab disk: Balanced | $0.000164384 per GiB-hour | |
| Colab disk: Standard | $0.000065753 per GiB-hour | |
| E2 vCPU and memory (Workbench) | Same as Colab Enterprise | |

- Colab Enterprise: "To calculate pricing, sum the costs of the virtual machines you use". The boot disk of new runtimes defaults to SSD. [Colab pricing](https://cloud.google.com/colab/pricing)
- Workbench: CPU is charged in STARTING, PROVISIONING, ACTIVE and similar states. Disk is also charged in STOPPED and SUSPENDED states. [Gemini platform pricing](https://cloud.google.com/vertex-ai/pricing)
- The same Workbench pricing section also shows separate "management fees" tables of "$0.05 per vCPU" and "$0.005 per vCPU" with no time unit visible in the extracted text. [Gemini platform pricing](https://cloud.google.com/vertex-ai/pricing). See Gaps.

**Regions**
- Colab Enterprise Americas regions: northamerica-northeast1, southamerica-east1, us-central1, us-east1, us-east4, **us-east5**, us-south1, us-west1, us-west2, us-west4. There are also many APAC and EU regions; europe-west10, asia-south2 and europe-west9 were added 2026-06-18. [Colab locations](https://docs.cloud.google.com/colab/docs/locations); [Colab release notes](https://docs.cloud.google.com/colab/docs/release-notes)
- Colab Enterprise runtimes use Compute Engine quota. [Schedule a notebook run](https://docs.cloud.google.com/colab/docs/schedule-notebook-run)

### Inferences
- **Hourly cost by machine** (us-central1, on demand, list prices above):
  - e2-standard-2 (2 vCPU / 8 GiB): 2×0.026174 + 8×0.003508 ≈ **$0.080/h** compute.
  - e2-standard-4 (4 vCPU / 16 GiB, the Colab default): ≈ **$0.161/h** compute.
  - Disk adds about $0.028/h for 100 GiB SSD (Colab default) or $0.016/h for 100 GiB balanced.
- **Machine size.** The job is network- and async-bound, so e2-standard-2 is plenty. The CPU table lists only "E2", so I can't confirm that shared-core types (e2-small, e2-medium) are allowed in Colab Enterprise templates.
- **Price column.** The Colab "Price" column looks all-in, meaning Compute Engine price plus the management fee. $0.026174 − $0.004362 ≈ $0.021812, which matches the usual Compute Engine E2 vCPU list price. Treat this as approximate.
- **Colab idle shutdown.** A long-running cell keeps the kernel busy. Based on the "no kernel activity" wording, it should not trigger idle shutdown, but no doc states this outright. A template with idle shutdown turned off (`0s`) removes the risk.
- **Workbench idle shutdown.** A `nohup python -m src.run ... &` started from a terminal produces CPU load but not kernel activity. The doc says CPU usage does not reset the timer, so the instance could be stopped mid-run. **Turn off idle shutdown or set it to 1440 minutes for terminal-launched runs**, then stop the instance manually.
- **Region choice.** Model calls go to the model's own endpoint (e.g. us-east5 or global for Claude), so the runtime region does not need to match the model region. us-central1 (cheapest listing) or us-east5 (same region as the Claude examples) are both reasonable.

### Gaps
- No official doc found listing which machine types (e.g. e2-small or e2-medium) Colab Enterprise runtime templates accept.
- The unit and scope of Workbench's "$0.05 per vCPU" and "$0.005 per vCPU" management-fee tables could not be determined from extracted text. They may be for legacy managed or user-managed notebooks. The per-machine-type Workbench table shows the same E2 all-in rates as Colab.
- The default machine type in the Workbench console "Create new" dialog was not stated in the docs fetched.
- Workbench docs do not say whether terminal websocket activity (`/api/terminals`) counts as "activity". Only kernel activity is stated.

## Q2. Getting the notebook from GitHub into each product, and pushing changes back

### Takeaway
- **Workbench** has a documented GitHub round trip: Git → Clone a Repository in JupyterLab (jupyterlab-git), commit in the Git tab, then Git → Push to Remote using a personal access token or SSH key.
- **Colab Enterprise** can only **import** a notebook from your computer, Cloud Storage, or a URL. There is no documented GitHub clone, open, or push. Colab notebooks are stored as Dataform-backed code assets, not in a git working tree. Keep GitHub as the source of truth and edit and push from a local clone.

### Cited Findings
**Colab Enterprise**
- Import path: **My notebooks** → choose Region → **Import** → "Import source" = Your computer, Cloud Storage, or **URL** ("enter the URL of the notebook file to import"). The notebook must be under 20 MB. [Colab quickstart](https://docs.cloud.google.com/colab/docs/create-console-quickstart). Page last updated 2026-11-10.
- Colab Enterprise requires the **Agent Platform, Dataform, and Compute Engine APIs**. Its roles include `dataform.repositories.*` permissions, so notebooks are Dataform repositories. [Colab quickstart](https://docs.cloud.google.com/colab/docs/create-console-quickstart); [Schedule a notebook run](https://docs.cloud.google.com/colab/docs/schedule-notebook-run)
- A 2024 forum thread reports that the consumer-Colab trick of swapping `github.com` for `colab.research.google.com/github` does not work in Colab Enterprise. It also says a repo can be cloned via the **Terminal**, but cloned `.ipynb` files open as raw files, "not rendered as a notebook and not executable". A Google reply said opening from GitHub was "currently not available". [Google Developer forums (Feb 2024)](https://discuss.google.dev/t/colab-enterprise-cloning-github-repos-and-opening-notebooks/145153). This is old, but I found no newer doc or release note adding GitHub integration through 2026-11-10 ([Colab release notes](https://docs.cloud.google.com/colab/docs/release-notes)).

**Workbench**
- Clone path: Instances → **Open JupyterLab** → pick a folder in the File Browser → **Git > Clone a Repository** → paste the HTTPS URL → Clone. [Save a notebook to GitHub](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/save-to-github). Page last updated 2026-11-20.
- Identity setup: **Git > Open Git Repository in Terminal**, then `git config --global user.name "USERNAME"` and `git config --global user.email "EMAIL_ADDRESS"`. You can optionally add an SSH key. [Save a notebook to GitHub](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/save-to-github)
- Push path: **Git** tab → Track or stage → enter a Summary → **Commit** → **Git > Push to Remote**. With 2FA, use a GitHub username plus personal access token. [Save a notebook to GitHub](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/save-to-github)

### Inferences
- **Colab, interactive use.** Pasting the `raw.githubusercontent.com/<org>/<repo>/<branch>/notebooks/base_config.ipynb` URL into Import → URL should work for a public repo, since the doc accepts any notebook URL. This is untested. The imported notebook is a copy, so edits do not flow back to GitHub.
- **Colab, push-back workflow.** Download the `.ipynb` from Colab Enterprise and commit it from a local clone. Alternatively, treat the repo notebook as a thin launcher you edit only locally or in Workbench.
- **Colab, headless execution.** Executions take the notebook from a GCS URI, a Dataform repository plus commit SHA, or direct content (see Q5), not from GitHub. Copy it up first with `gcloud storage cp notebooks/base_config.ipynb gs://BUCKET/notebooks/`.
- **The code itself** can be pulled at run time in both products with a `!git clone --depth 1 https://github.com/<org>/<repo>.git` cell. Colab runtimes have public internet access unless a template turns it off (`--no-enable-internet-access`).

### Gaps
- No 2026 doc confirms whether Colab Enterprise "Import → URL" accepts `raw.githubusercontent.com` URLs, or whether a Colab Enterprise terminal is still offered.
- No documented Colab Enterprise → GitHub push or sync feature was found.

## Q3. Authentication inside the runtime (ADC) and IAM roles for Vertex models including Claude

### Takeaway
**Colab Enterprise:** the default runtime and any template with EUC enabled expose **your user credentials to ADC**. After a one-time consent dialog, `AnthropicVertex(...)` and `google-genai` just work with your identity.

**Workbench:** ADC resolves to the **instance's service account** through the metadata server. That service account needs the roles, not you.

**Roles in both cases:**
- `roles/aiplatform.user` on whoever makes the calls.
- `roles/consumerprocurement.entitlementManager` for whoever enables Claude in Model Garden (one time).
- The Cloud Commerce Consumer Procurement API must be allowed by org policy.

### Cited Findings
- ADC search order:
  1. the `GOOGLE_APPLICATION_CREDENTIALS` environment variable;
  2. the file created by `gcloud auth application-default login`;
  3. the attached service account from the metadata server.

  [How ADC works](https://docs.cloud.google.com/docs/authentication/application-default-credentials) (last updated 2026-11-17)

**Colab Enterprise**
- "By default Colab Enterprise notebooks use your user credentials to authenticate and authorize code that interacts with other Google Cloud services… the notebook's code has the same level of access to Google Cloud that the user does." [Colab introduction](https://docs.cloud.google.com/colab/docs/introduction)
- "The default runtime has end-user credentials enabled." On first connect, a Sign in dialog asks you to grant "See, edit, configure, and delete your Google Cloud data…". [Connect to a runtime](https://docs.cloud.google.com/colab/docs/connect-to-runtime); [Colab quickstart](https://docs.cloud.google.com/colab/docs/create-console-quickstart)
- EUC must be chosen when the template is created and "can't be modified later". [Access Google Cloud services and APIs](https://docs.cloud.google.com/colab/docs/run-code-adc)
- Without EUC, you can run `!gcloud auth application-default login` inside the notebook. This writes an ADC file onto the runtime VM. [Access Google Cloud services and APIs](https://docs.cloud.google.com/colab/docs/run-code-adc)
- Required roles:
  - `roles/aiplatform.colabEnterpriseUser`: create notebooks and run them on a runtime ([Colab quickstart](https://docs.cloud.google.com/colab/docs/create-console-quickstart)).
  - `roles/aiplatform.colabEnterpriseAdmin`: listed by the ADC page for accessing Google Cloud services from a notebook ([Access Google Cloud services and APIs](https://docs.cloud.google.com/colab/docs/run-code-adc)) and needed to create runtimes and templates ([Create a runtime](https://docs.cloud.google.com/colab/docs/create-runtime)).

**Workbench**
- The instance uses a service account (the Compute Engine default or a custom one in the same project). "If the instance needs to access other Google Cloud resources, this service account must also have access." The service account can't be changed after creation. [Manage access to JupyterLab](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/manage-access-jupyterlab); [Workbench create](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/create)
- In "Single user only" access mode, a user who is not the creator needs `roles/iam.serviceAccountUser` on the instance's service account. Group access is not supported. [Manage access to JupyterLab](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/manage-access-jupyterlab)

**Partner models (Claude and others)**
- Two requirements:
  1. **Consumer Procurement Entitlement Manager** (`roles/consumerprocurement.entitlementManager`). "Anyone who's been granted this role can enable partner models in Model Garden."
  2. The `aiplatform.endpoints.predict` permission, which is included in **Agent Platform User** (`roles/aiplatform.user`).

  Commands from the doc: `gcloud projects add-iam-policy-binding PROJECT_ID --member=PRINCIPAL --role=roles/consumerprocurement.entitlementManager` and the same with `--role=roles/aiplatform.user`. [Use partner models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/use-partner-models) (last updated 2026-11-20)
- Org policy must allow `cloudcommerceconsumerprocurement.googleapis.com`. Any Model Garden model-access policy must allow partner models. [Use partner models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/use-partner-models)
- Reseller restriction: "If your Google Cloud billing account is managed by a prohibited reseller, you will be unable to accept the Terms of Service or enable Claude models." This is worth checking for university-provided billing. [Use partner models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/use-partner-models)
- Claude Python sample: `pip install -U 'anthropic[vertex]'`, `gcloud auth application-default login`, then `AnthropicVertex(project_id=PROJECT_ID, region="us-east5")` with `model="claude-sonnet-4-6"`. Global and multi-region endpoints are also documented. [Use Claude](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude/use-claude)
- Claude quotas:
  - QPM and TPM are per endpoint type.
  - Example: Claude Opus 4.6 gets 200 QPM in us-east5 and 400 QPM on the global endpoint.
  - Models launched after 2026-05-26 use shared "lineage" quotas on global and multi-region endpoints.

  [Claude quotas](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude/quotas)

### Inferences
- In Colab Enterprise with EUC, each student's own account needs `roles/aiplatform.user`, plus the Colab roles. Claude must have been enabled once in Model Garden by someone holding `roles/consumerprocurement.entitlementManager`.
- In Workbench, grant `roles/aiplatform.user` and `roles/secretmanager.secretAccessor` (Q4) to the instance's service account. Granting them to the student is not enough.
- Prefer a dedicated service account over the Compute Engine default one, which may carry broad or narrow grants depending on org policy.
- About 11,000 calls in 2–4 hours is roughly 45–90 requests per minute. That is under the documented per-region Claude QPM quotas above, though TPM may bind first for long prompts.

### Gaps
- No doc fetched says whether `google-auth` warns about a missing quota project when using Colab EUC credentials against `aiplatform.googleapis.com`.
- I did not verify which specific Claude, Gemini, or Llama model IDs the team uses. Other notes cover the models themselves.

## Q4. Secrets: keeping an Anthropic API key out of the committed notebook

### Takeaway
Store the key in **Secret Manager** and read it at run time with `google-cloud-secret-manager` (or `gcloud secrets versions access latest --secret=...`) through ADC. Put it into `os.environ["ANTHROPIC_API_KEY"]` without printing it. Colab Enterprise has no documented equivalent of consumer Colab's "Secrets" (`google.colab.userdata`) panel.

If all Claude calls go through Vertex (`AnthropicVertex`), **no Anthropic API key is needed at all**, because ADC authenticates the calls.

### Cited Findings
- Reading a secret requires **Secret Manager Secret Accessor** (`roles/secretmanager.secretAccessor`) on the secret. CLI: `gcloud secrets versions access VERSION_ID --secret=SECRET_ID`. Console: Secret Manager → secret → versions. [Access a secret version](https://docs.cloud.google.com/secret-manager/docs/access-secret-version) (last updated 2026-11-12)
- The Secret Manager doc warns not to print the secret payload in sample code. [Access a secret version](https://docs.cloud.google.com/secret-manager/docs/access-secret-version)
- Third-party, not official: a Google Cloud Community answer and a Medium post say consumer Colab's Secrets feature is **not available in Colab Enterprise** and recommend Secret Manager via the Python client. [Medium – Using API keys in a Colab notebook](https://medium.com/google-cloud/using-api-keys-and-other-sensitive-data-in-a-colab-notebook-c2feba57c4e0) (seen via search snippet only). I found no official Colab Enterprise "secrets" doc; `docs.cloud.google.com/colab/docs/secrets` returns 404.
- Colab Enterprise notebook code runs with the user's credentials through ADC when EUC is enabled ([Access Google Cloud services and APIs](https://docs.cloud.google.com/colab/docs/run-code-adc)). Secret Manager access is therefore governed by the student's own IAM grants.

### Inferences
Recommended notebook cell (no key in the file):

```python
import os
from google.cloud import secretmanager
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "<project-id>")
name = f"projects/{PROJECT_ID}/secrets/anthropic-api-key/versions/latest"
os.environ["ANTHROPIC_API_KEY"] = secretmanager.SecretManagerServiceClient().access_secret_version(name=name).payload.data.decode()
```

- The Secret Manager API (`secretmanager.googleapis.com`) is **not** among the APIs the project has enabled (aiplatform, notebooks), so it must be enabled.
- One-time setup uses standard gcloud syntax, not re-verified in this session:

  ```
  gcloud services enable secretmanager.googleapis.com
  printf %s "$KEY" | gcloud secrets create anthropic-api-key --data-file=- --replication-policy=automatic
  gcloud secrets add-iam-policy-binding anthropic-api-key --member=user:STUDENT@... --role=roles/secretmanager.secretAccessor
  ```
- Repo hygiene:
  - Clear notebook outputs before committing (e.g. `nbstripout` as a git filter).
  - Never `print(os.environ)`.
  - Keep `.env` in `.gitignore` for local runs.

### Gaps
- No official Google doc confirms or denies a Colab Enterprise secrets panel as of Nov 2026.
- The `gcloud secrets create` and `add-iam-policy-binding` syntax was not re-fetched in this session.

## Q5. Keeping a multi-hour job alive and writing outputs durably (GCS / persistent disk)

### Takeaway
**Colab Enterprise:** the robust path is a **one-off notebook execution** (console: Notebook actions → **Schedule** → One-off). It runs headless on a runtime built from a template, independent of your browser. The default `--execution-timeout` is 24h, and the executed notebook is written to a GCS bucket. Interactive sessions work for smoke tests, but a closed tab is not guaranteed to keep the run alive.

**Workbench:** run the CLI under `tmux` or `nohup` from the JupyterLab terminal on the persistent data disk. **Turn off idle shutdown**, because CPU activity does not count. Periodically copy JSONL to GCS.

### Cited Findings
**Colab Enterprise executions**
- You can schedule a notebook "to run immediately for one time, or on a recurring schedule. Colab Enterprise stores the results in Cloud Storage". [Colab introduction](https://docs.cloud.google.com/colab/docs/introduction)
- Console path: **My notebooks** → Region → notebook ⋮ **Notebook actions** → **Schedule** → name → Runtime template → Run schedule **One-off** → Cloud Storage output location (Browse or Create new bucket) → Service account field (only if the template has no EUC) → **Submit**. "The notebook run starts immediately." [Schedule a notebook run](https://docs.cloud.google.com/colab/docs/schedule-notebook-run). Page last updated 2026-06-18.
- Identity: with EUC on the template, the run "uses the permissions associated with your user credentials". Otherwise you must specify a service account. [Schedule a notebook run](https://docs.cloud.google.com/colab/docs/schedule-notebook-run)
- Roles for the principal that runs the notebook:
  - `roles/dataform.codeViewer` on the notebook;
  - `roles/logging.logWriter` and `roles/monitoring.metricWriter` on the project;
  - `roles/storage.legacyBucketWriter` (the doc says "on the notebook");
  - `roles/storage.legacyObjectReader` on the output bucket.

  [Schedule a notebook run](https://docs.cloud.google.com/colab/docs/schedule-notebook-run)
- CLI synopsis: `gcloud colab executions create --display-name=... --gcs-output-uri=... --notebook-runtime-template=...`, plus exactly one notebook source:
  - `--direct-content`, or
  - `--dataform-repository-name` with `--commit-sha`, or
  - `--gcs-notebook-uri` (optional `--generation`).

  It also takes exactly one of `--service-account` or `--user-email`, and `--execution-timeout` ("The max running time of the execution job", **default "24h"**), `--async`, and `--region`. [gcloud colab executions create](https://docs.cloud.google.com/sdk/gcloud/reference/colab/executions/create). Page last updated 2026-05-27.
- Terraform examples set `execution_timeout = "86400s"`. [Schedule a notebook run](https://docs.cloud.google.com/colab/docs/schedule-notebook-run)

**Colab Enterprise interactive sessions**
- Runtimes can be stopped, disconnected via Runtime → **Manage sessions**, reconnected, or deleted. [Manage runtimes](https://docs.cloud.google.com/colab/docs/manage-runtimes)
- Idle shutdown only happens when no notebook is connected and there is no kernel activity. [Colab idle shutdown](https://docs.cloud.google.com/colab/docs/idle-shutdown)

**Workbench**
- Idle shutdown ignores CPU usage. Only kernel activity or new notebook output resets the timer. [Workbench idle shutdown](https://docs.cloud.google.com/vertex-ai/docs/workbench/instances/idle-shutdown)
- The Workbench **executor** runs notebooks on a schedule and stores output in a GCS bucket. "If your instance is shut down, the executor still runs your notebook file on schedule."
- The instance's service account needs `roles/notebooks.runner` and `roles/storage.admin` for the executor.
- In JupyterLab 4 the executor snapshots the notebook into GCS, so edits need a new schedule.

  [Workbench schedule a notebook run](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/instances/schedule-notebook-run-quickstart)
- Since 2026-09-09, a Workbench scheduled run can use **your user account** as its execution identity, so ADC inside resolves to you. It can also use a custom VM image or container. This needs `scheduler-jupyter-plugin` ≥ 0.1.8. [Workbench release notes](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/release-notes)
- Workbench data and boot disks (100 GB PD_STANDARD each by default) keep being billed while the instance is stopped. [gcloud workbench instances create](https://docs.cloud.google.com/sdk/gcloud/reference/workbench/instances/create); [Gemini platform pricing](https://cloud.google.com/vertex-ai/pricing)

### Inferences
- **Colab execution recipe.** The notebook should:
  1. `git clone` the repo;
  2. `pip install -r requirements.txt`;
  3. load secrets;
  4. run `python -m src.run --model X` with `subprocess.run(..., check=True)` (a long cell keeps the kernel busy);
  5. then run `src.judge` and `src.analyze`;
  6. `gcloud storage rsync` (or `gsutil -m rsync -r`) the results directory to `gs://BUCKET/results/` after each step.

  The runtime disk is not durable once the execution's runtime is gone, so **GCS is the durable store**.
- **Parameterising the model.** Use either one execution per model (edit a `MODEL = "..."` cell, upload, launch) or one execution that loops over models. Set `--execution-timeout=12h` or more for three models at 2–4h each.
- **Resumability.** The harness appends JSONL. To resume after a failure, the notebook should first `gcloud storage rsync gs://BUCKET/results/ results/` (pull existing JSONL down), then rerun.
- **Interactive Colab and Workbench JupyterLab.** Closing the browser normally leaves the server-side kernel running (standard Jupyter behaviour), but cell output produced while disconnected is lost. The harness writes JSONL to disk, so data survives, but the docs make no guarantee. Use executions (Colab) or `tmux`/`nohup` plus idle shutdown turned off (Workbench) for anything over the 3h idle default.
- **Workbench recipe:**

  ```
  tmux new -s run
  cd ~/repo && python -m src.run --model X 2>&1 | tee logs/X.log
  ```

  Set `gcloud workbench instances update INSTANCE --location=ZONE --metadata=idle-timeout-seconds=` to turn idle shutdown off. `--location` is likely required; the doc example omits it. Add a cron or loop that runs `gcloud storage rsync results gs://BUCKET/results --recursive`. Stop the instance when finished.

### Gaps
- No doc states the maximum allowed Colab `--execution-timeout`. Only the 24h default was seen.
- No doc fetched describes how to pass parameters (papermill-style) to a Colab Enterprise execution.
- No official statement says what happens to a running cell in Colab Enterprise when the browser tab closes.
- The `gcloud storage rsync` syntax and the Workbench `/home/jupyter` data-disk mount point were not re-verified in this session.

## Q6. Running the notebook locally (VS Code / Jupyter) against Vertex with user ADC

### Takeaway
Local runs work with `gcloud auth application-default login`. The official Claude-on-Vertex sample assumes exactly this. Set a quota project with `gcloud auth application-default set-quota-project PROJECT_ID` to avoid "no quota project" or "API not enabled" errors with user credentials. The laptop must stay awake for 2–4h per model, which is the main practical drawback.

### Cited Findings
- Create local credentials with `gcloud auth application-default login`. This is not needed in Cloud Shell. [Set up ADC for local dev](https://docs.cloud.google.com/docs/authentication/set-up-adc-local-dev-environment) (last updated 2026-11-17)
- User-account ADC "might not work for some APIs without extra configuration". The local ADC file holds a refresh token; revoke it with `gcloud auth application-default revoke`. The ADC file is tied to the user account, not the gcloud configuration. [Set up ADC for local dev](https://docs.cloud.google.com/docs/authentication/set-up-adc-local-dev-environment)
- Client-based APIs need a **quota project** when called with user credentials. Ways to set it:
  - `gcloud auth application-default set-quota-project YOUR_PROJECT`;
  - `gcloud config set billing/quota_project YOUR_PROJECT` (for gcloud only);
  - the `x-goog-user-project` header.

  The API must be enabled in that project, and you need `serviceusage.services.use` (in **Service Usage Consumer**). [Troubleshoot ADC](https://docs.cloud.google.com/docs/authentication/troubleshoot-adc)
- The Claude-on-Vertex Python sample's setup comments are `gcloud auth application-default login` and `pip3 install -U 'anthropic[vertex]'`. [Use Claude](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude/use-claude)

### Inferences
- Local setup:

  ```
  gcloud auth login
  gcloud config set project PROJECT_ID
  gcloud auth application-default login
  gcloud auth application-default set-quota-project PROJECT_ID
  ```

  The student's account needs `roles/aiplatform.user` and `roles/serviceusage.serviceUsageConsumer` (owners and editors already have both).
- Local runs avoid notebook-runtime cost entirely. However, laptop sleep, VPN changes, or Wi-Fi drops can interrupt a 2–4h job. The harness's resumability makes that tolerable, and `caffeinate -i` on macOS helps.

### Gaps
- I did not verify whether `aiplatform.googleapis.com` is classified as client-based (quota project strictly required) or resource-based. Setting the quota project is harmless either way.

## Q7. Approximate runtime cost for ~8 hours, and recommended setup

### Takeaway
Runtime cost is roughly **$0.7–$1.6 for 8 hours** of a single E2 notebook VM in us-central1. Workbench adds about $0.30/day of standing disk cost (my estimate) if the instance is kept. LLM API charges for 11k calls per model will be far larger.

**Recommendation:** use **Colab Enterprise** with a custom CPU runtime template (e2-standard-2, EUC on, idle shutdown off or 24h). Run each model as a **one-off notebook execution** that clones the public repo, reads the key from Secret Manager, and rsyncs JSONL to GCS. Use **Workbench** only if the team wants a persistent VM with terminal and git push.

### Cited Findings
- E2 rates and disk rates as cited in Q1 ([Colab pricing](https://cloud.google.com/colab/pricing); [Gemini platform pricing](https://cloud.google.com/vertex-ai/pricing)).
- Workbench disks keep billing while STOPPED ([Gemini platform pricing](https://cloud.google.com/vertex-ai/pricing)).

### Inferences

**8-hour cost estimates** (us-central1, on demand, calculated from the cited rates):

| Setup | Hourly | 8 hours |
|---|---|---|
| Colab default runtime: e2-standard-4 + 100 GiB SSD | 0.1608 + 0.0279 ≈ $0.19 | **≈ $1.51** |
| Colab custom template: e2-standard-2 + 100 GiB balanced | 0.0804 + 0.0164 ≈ $0.097 | **≈ $0.77** |
| Workbench: e2-standard-2 compute only | ≈ $0.08 | **≈ $0.64** |

- For the Workbench row, add 200 GiB of PD-standard (boot + data) at about $0.0000658 per GiB-hour. That is about $0.013/h, or about **$9–10/month while the instance exists, even when stopped**. I applied Colab's standard-disk rate as a proxy.

**Recommended setup (Colab Enterprise, primary):**

1. **APIs.** Enable `dataform.googleapis.com`, `compute.googleapis.com` and `secretmanager.googleapis.com`. aiplatform and notebooks are already enabled. Colab Enterprise requires Dataform and Compute Engine ([Colab quickstart](https://docs.cloud.google.com/colab/docs/create-console-quickstart)).
2. **IAM per student:**
   - `roles/aiplatform.colabEnterpriseUser`, or `roles/aiplatform.colabEnterpriseAdmin` to create templates;
   - `roles/aiplatform.user`;
   - `roles/secretmanager.secretAccessor` on the secret;
   - the execution roles from Q5;
   - object read/write on the results bucket.

   One person with `roles/consumerprocurement.entitlementManager` enables Claude (and any Llama MaaS model) in Model Garden once.
3. **Runtime template** (one-time):

   ```
   gcloud colab runtime-templates create --display-name="cs546-cpu" \
     --region=us-central1 --machine-type=e2-standard-2 \
     --disk-type=PD_BALANCED --disk-size-gb=50 --idle-shutdown-timeout=0s
   ```

   EUC and internet access are on by default. Flags are from the 2026-06 gcloud reference. You can optionally make it the region's default runtime template (feature added 2026-09-28).
4. **Getting the notebook in:**
   - Interactive smoke test: My notebooks → Import → URL (raw GitHub URL, unverified) or Your computer.
   - Long runs: `gcloud storage cp notebooks/base_config.ipynb gs://BUCKET/notebooks/` from a local clone.
5. **Notebook cells:**
   1. `!git clone --depth 1 https://github.com/<org>/<repo>.git && pip install -r <repo>/requirements.txt`
   2. Load the key from Secret Manager, only if using the direct Anthropic API.
   3. `gcloud storage rsync` existing results down (resume).
   4. `subprocess.run(["python","-m","src.run","--model",MODEL], check=True)`, then `src.judge` and `src.analyze`.
   5. `gcloud storage rsync` results up.

   ADC needs no code: EUC supplies the user's credentials, and `AnthropicVertex(project_id=..., region="us-east5" or "global")` picks them up.
6. **Launch headless:**

   ```
   gcloud colab executions create --display-name=run-MODEL \
     --notebook-runtime-template=cs546-cpu \
     --gcs-notebook-uri=gs://BUCKET/notebooks/base_config.ipynb \
     --gcs-output-uri=gs://BUCKET/executions \
     --user-email=STUDENT@... --execution-timeout=12h --region=us-central1
   ```

   Or use the console: Notebook actions → Schedule → One-off. Monitor from the Executions list and GCS.
7. **Edits flow back to GitHub** only through a local clone (VS Code). Colab Enterprise copies are not git-linked.

**Alternative (Workbench):**

1. Create an instance with:

   ```
   gcloud workbench instances create cs546-wb --location=us-central1-a \
     --machine-type=e2-standard-2 --service-account-email=SA@PROJECT.iam.gserviceaccount.com \
     --metadata=idle-timeout-seconds=86400
   ```

   The service account needs `roles/aiplatform.user` and `roles/secretmanager.secretAccessor`. Students need `roles/iam.serviceAccountUser` on it (single-user mode).
2. Git → Clone a Repository, with a PAT for pushes.
3. Run in `tmux` from the terminal.
4. rsync results to GCS.
5. **Stop the instance when done**; disks still bill. Consider turning off Antigravity (`enable-antigravity=false`) if unwanted.

### Gaps
- Exact per-region prices for us-east5 were not extracted. The rates above are the default-rendered (Iowa) column.
- The cost estimate excludes Claude, Gemini and Llama token charges, which other notes should cover.
- The Colab `--disk-size-gb` minimum (10 GB) was cited, but whether a 50 GB balanced disk works smoothly with the Colab image size was not verified.
