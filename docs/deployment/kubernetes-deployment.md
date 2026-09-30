# Deploying MavrickGPT on Kubernetes

This guide explains **how MavrickGPT works**, how to **deploy it to a cluster**
with Helm, how to enable the **LibreChat web UI**, and how the **operator** runs
24/7 health checks.

> MavrickGPT is an open-source AI SRE agent (a Hacktoberfest rebrand + extension
> of HolmesGPT). It investigates production incidents by autonomously calling
> read-only tools until it can explain the root cause.

---

## 1. How it works

```
                 ┌──────────────────────────────────────────────┐
   alert / ask   │                MavrickGPT pod                 │
 ───────────────▶│  ┌────────────┐   pick tool    ┌───────────┐  │
                 │  │ Agentic    │ ─────────────▶ │ Toolsets  │  │──▶ Prometheus
   LibreChat UI  │  │ tool loop  │ ◀───────────── │ (k8s,...) │  │──▶ Kubernetes API
 ───────────────▶│  └────────────┘   read result  └───────────┘  │──▶ Loki / Datadog / ...
                 └──────────────────────────────────────────────┘
                          │ HTTP API :5050 (/api/chat, /healthz)
                          ▼
                 answers, root-cause, remediation suggestions
```

- The **agentic loop** (`mavrick/core/tool_calling_llm.py`) lets the LLM choose a
  tool, read the real result, and iterate until solved — no fixed script.
- **Toolsets** (`mavrick/plugins/toolsets/`) are read-only integrations:
  Kubernetes, Prometheus, Grafana, Loki, Datadog, AWS, and more.
- The pod serves an **HTTP API** on `:5050` (`server.py`) — `/api/chat`,
  `/healthz`, `/readyz`.
- Any LLM provider works (OpenAI, Anthropic, Azure, Bedrock, Gemini) and
  **open-weight models via Ollama** — the Hacktoberfest focus.

---

## 2. Prerequisites

| Requirement | Notes |
| --- | --- |
| Kubernetes 1.24+ | `kind`, `minikube`, EKS/GKE/AKS all work |
| `kubectl` + `helm` 3.x | configured against the target cluster |
| An LLM API key | e.g. `OPENAI_API_KEY` (or point at Ollama) |

---

## 3. Quick deploy

```bash
# 1) Namespace
kubectl create namespace mavrick

# 2) Provide your LLM key as a secret and reference it from the chart
kubectl -n mavrick create secret generic mavrick-llm \
  --from-literal=OPENAI_API_KEY="sk-..."

# 3) Install the chart
helm install mavrick ./helm/mavrick \
  --namespace mavrick \
  --set additionalEnvVars[0].name=MODEL \
  --set additionalEnvVars[0].value=gpt-4o \
  --set extraEnvVarsSecrets[0]=mavrick-llm

# 4) Check it is healthy
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

---

## 4. Enable the LibreChat web UI

[LibreChat](https://www.librechat.ai/) is an open-source chat UI. The chart ships
an opt-in deployment (UI + MongoDB) preconfigured with a **MavrickGPT** endpoint.

```bash
helm upgrade mavrick ./helm/mavrick -n mavrick \
  --reuse-values \
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

> Security: override `librechat.secrets.*` (JWT/creds keys) with your own values
> in production — the defaults are placeholders.

### Local models (open-weight, no API key)

Run Ollama and point `MODEL` at it, e.g. `--set additionalEnvVars[0].value=ollama/llama3.1`.
LibreChat then talks to the same MavrickGPT backend.

---

## 5. Operator mode (24/7 health checks)

The chart also deploys the **MavrickGPT operator** (`operator-deployment.yaml`),
which runs scheduled health checks and proactively investigates problems before
users notice — see [`operator.md`](./operator.md) for how it works and how to
define checks.

---

## 6. Uninstall

```bash
helm uninstall mavrick -n mavrick
kubectl delete namespace mavrick
```

---

## 7. Troubleshooting

| Symptom | Fix |
| --- | --- |
| Pod `CrashLoopBackOff` | `kubectl -n mavrick logs deploy/mavrick-mavrick` — usually a missing/invalid LLM key |
| `/api/chat` returns 401/empty | LLM key not set or wrong provider for `MODEL` |
| LibreChat can't reach agent | confirm `mavrick-mavrick` service is up; check `librechat.mavrickApiUrl` |
| No tool data | the relevant toolset (Prometheus/k8s) isn't configured or lacks RBAC |
