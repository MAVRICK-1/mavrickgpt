# MavrickGPT — Deploy on a Cluster

One guide for everything you need to run MavrickGPT in Kubernetes:

1. [Build the CLI & image](#0-build-the-cli--image)
2. [How it works](#1-how-it-works)
3. [Deploy to a cluster](#2-deploy-to-a-cluster)
4. [Enable the LibreChat web UI](#3-enable-the-librechat-web-ui)
5. [Operator mode (24/7 checks)](#4-operator-mode-247-checks)
6. [Troubleshooting](#5-troubleshooting)

> MavrickGPT is an open-source AI SRE agent. It investigates incidents by
> autonomously calling **read-only** tools until it can explain the root cause.
> Any LLM works (OpenAI, Anthropic, Azure, Bedrock, **Gemini**) including
> **open-weight models via Ollama**.

---

## 0. Build the CLI & image

MavrickGPT is a Python/Poetry project. The `mavrick` CLI entry point is defined in
`pyproject.toml` (`mavrick = "mavrick.main:run"`, package `mavrick`).

### Build & install the CLI (from source)

```bash
git clone https://github.com/MAVRICK-1/mavrickgpt.git
cd mavrickgpt

# option A: dev/editable install (recommended while hacking)
poetry install
poetry run mavrick version
poetry run mavrick ask -i

# option B: build a wheel and install it anywhere
poetry build                       # -> dist/mavrickgpt-*.whl
pip install dist/mavrickgpt-*.whl  # installs the `mavrick` command
mavrick version
```

The CLI needs an LLM key at runtime (e.g. `export GEMINI_API_KEY=...` +
`export MODEL=gemini/gemini-flash-lite-latest`) — open-weight models via Ollama
need no key.

### Build the container image

The `Dockerfile` builds the same code as a server image (entry `mavrick_cli.py`;
the chart overrides the command to `python3 -u server.py`).

```bash
docker build -t mavrick:0.0.0 .

# load it into a local kind cluster (no registry needed)
kind load docker-image mavrick:0.0.0 --name mavrick
docker tag mavrick:0.0.0 robustadev/mavrick:0.0.0   # matches chart default registry/image
```

The chart pulls `{{ .Values.registry }}/{{ .Values.image }}` (default
`robustadev/mavrick:0.0.0`, `imagePullPolicy: IfNotPresent`), so a locally loaded
image is used as-is.

---

---

## 1. How it works

```
                 ┌──────────────────────────────────────────────┐
   alert / ask   │                MavrickGPT pod                 │
 ───────────────▶│  ┌────────────┐   pick tool    ┌───────────┐  │──▶ Kubernetes API
                 │  │ Agentic    │ ─────────────▶ │ Toolsets  │  │──▶ Prometheus
   LibreChat UI  │  │ tool loop  │ ◀───────────── │ Toolsets  │  │──▶ Loki / Datadog / ...
 ───────────────▶│  └────────────┘   read result  └───────────┘  │──▶ AWS / Azure / ArgoCD
                 └──────────────────────────────────────────────┘
                          │ HTTP API :5050 (/api/chat, /healthz)
                          ▼
                 answers, root-cause, remediation suggestions
```

- The **agentic loop** (`mavrick/core/tool_calling_llm.py`) lets the LLM pick a
  tool, read the real result, and iterate until solved — no fixed script.
- **Toolsets** (`mavrick/plugins/toolsets/`) are read-only
  integrations: Kubernetes, Prometheus, Grafana, Loki, Datadog, AWS, Azure,
  ArgoCD, databases, and more.
- The pod serves an **HTTP API** on `:5050` (`server.py`): `/api/chat`,
  `/healthz`, `/readyz`.

---

## 2. Deploy to a cluster

### Prerequisites

| Requirement | Notes |
| --- | --- |
| Kubernetes 1.24+ | `kind`, `minikube`, EKS/GKE/AKS all work |
| `kubectl` + `helm` 3.x | configured against the target cluster |
| An LLM API key | e.g. `GEMINI_API_KEY` / `OPENAI_API_KEY` (or point at Ollama) |

### Steps

```bash
# 1) Namespace
kubectl create namespace mavrick

# 2) Put your LLM key in a Secret (never commit keys to git)
kubectl -n mavrick create secret generic mavrick-llm-keys \
  --from-literal=GEMINI_API_KEY="AQ...."      # or OPENAI_API_KEY=sk-...

# 3) Install the chart, referencing the Secret + choosing a model
helm install mavrick ./helm/mavrick -n mavrick \
  --set 'extraEnvVarsSecrets[0]=mavrick-llm-keys' \
  --set 'modelList.gemini-flash.model=gemini/gemini-2.0-flash' \
  --set 'modelList.gemini-flash.api_key=envRef:GEMINI_API_KEY'

# 4) Verify
kubectl -n mavrick rollout status deploy/mavrick-mavrick
kubectl -n mavrick port-forward svc/mavrick-mavrick 5050:80 &
curl -s localhost:5050/healthz     # -> {"status":"healthy"}
```

Ask a question through the API:

```bash
curl -s localhost:5050/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"ask":"why is the checkout pod crashlooping?"}'
```

> `extraEnvVarsSecrets` mounts every key in the Secret as an env var, and
> `api_key: envRef:GEMINI_API_KEY` rewrites to the runtime `{{ env.GEMINI_API_KEY }}`
> so you never repeat the key value in the chart.

### Open-weight / local models (no API key)

Run Ollama and register a local model instead:

```bash
helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values \
  --set 'modelList.llama.model=ollama/llama3.1'
```

### Uninstall

```bash
helm uninstall mavrick -n mavrick && kubectl delete namespace mavrick
```

---

## 3. Enable the LibreChat web UI

[LibreChat](https://www.librechat.ai/) is an open-source chat UI. The chart ships
an **opt-in** deployment (UI + MongoDB) preconfigured with a **MavrickGPT** endpoint.

```bash
helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values \
  --set librechat.enabled=true

kubectl -n mavrick rollout status deploy/mavrick-librechat
kubectl -n mavrick port-forward svc/mavrick-librechat 3080:80
# open http://localhost:3080  ->  register  ->  pick the "MavrickGPT" model
```

Expose it publicly with an ingress:

```bash
helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values \
  --set librechat.enabled=true \
  --set librechat.ingress.enabled=true \
  --set librechat.ingress.className=nginx \
  --set librechat.ingress.host=mavrick.example.com
```

> Security: override `librechat.secrets.*` (JWT/creds keys) in production — the
> defaults are placeholders.

---


## 4. Operator mode (24/7 checks)

The chart also ships an **operator** (disabled by default) that runs scheduled
health checks and proactively investigates problems before users notice.

### How the operator works

```
  ScheduledHealthCheck (cron + prompt)
             │  operator watches the CR
             ▼
      mavrick-operator  ──HTTP /api/chat──▶  mavrick-mavrick (agent API)
             │                                     │ runs toolsets
             ▼                                     ▼
   TriggeredHealthCheck (one run)          live cluster data → verdict
             │
             ▼   (mode: alert)
     Slack / PagerDuty / ...
```

- The operator is a **separate Deployment** with its own image
  (`mavrick_operator/`, built from `Dockerfile.operator`). It does **not** call
  the LLM directly — on each cron tick it POSTs the check's `prompt` to the main
  **`mavrick-mavrick` API** (`operator.mavrickApiUrl`, default
  `http://<release>-mavrick:80`), which investigates with its toolsets.
- Because the investigation runs in the main agent pod, the operator **inherits
  that pod's model** (e.g. your Gemini/Copilot config). Override per check with
  `spec.model`.
- It watches three CRDs (installed by the chart under `crds/`):
  `healthchecks`, `scheduledhealthchecks`, `triggeredhealthchecks` `.mavrickgpt.dev`.

### Build the operator image

```bash
docker build -f Dockerfile.operator -t ghcr.io/<you>/mavrick-operator:0.0.0 .
kind load docker-image ghcr.io/<you>/mavrick-operator:0.0.0 --name mavrick   # local kind
# or: docker push ghcr.io/<you>/mavrick-operator:0.0.0                        # real registry
```

Point the chart at it with `operator.registry` / `operator.image`.

### Enable it

```bash
helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values \
  --set operator.enabled=true \
  --set operator.registry=ghcr.io/<you> \
  --set operator.image=mavrick-operator:0.0.0
kubectl -n mavrick rollout status deploy/mavrick-operator
```

### Define a check

```yaml
apiVersion: mavrickgpt.dev/v1
kind: ScheduledHealthCheck
metadata:
  name: checkout-latency
  namespace: mavrick
spec:
  schedule: "*/5 * * * *"      # cron
  enabled: true
  prompt: "Is the checkout service healthy? Check error rate and p95 latency."
  mode: alert                   # 'alert' notifies on failure, 'monitor' just logs
  timeout: 300
  # model: copilot-gpt4o        # optional per-check model override
  destinations:
    - type: slack               # alert target (only used in 'alert' mode)
```

```bash
kubectl apply -f checkout-latency.yaml
kubectl -n mavrick get scheduledhealthchecks
kubectl -n mavrick get triggeredhealthchecks   # individual runs
kubectl -n mavrick logs deploy/mavrick-operator
```

Key `values.yaml` settings live under `operator:` (`enabled`, `registry`, `image`,
`mavrickApiUrl`, `mavrickApiTimeout`, `logLevel`, `cleanupCompletedChecks`).

---

## 5. Troubleshooting

| Symptom | Fix |
| --- | --- |
| Pod `CrashLoopBackOff` | `kubectl -n mavrick logs deploy/mavrick-mavrick` — usually a missing/invalid LLM key |
| `/api/chat` returns 401/empty | LLM key not set, or `model`/provider mismatch |
| LibreChat can't reach agent | confirm `mavrick-mavrick` service is up; check `librechat.mavrickApiUrl` |
| No tool data | the relevant toolset (Prometheus/k8s) isn't enabled or lacks RBAC |
