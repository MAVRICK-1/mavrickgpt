# MavrickGPT — The Open-Source AI SRE Agent

MavrickGPT is an open-source AI agent that investigates production incidents and
finds root causes. It works with any stack — Kubernetes, VMs, cloud providers,
databases, and SaaS platforms — and with any LLM (OpenAI, Anthropic, Gemini, or
open-weight models via Ollama).


---

## Table of Contents

- [What it does](#what-it-does)
- [Install](#install)
- [Set an LLM key](#set-an-llm-key)
- [Run it](#run-it)
- [Build & deploy the CLI](#build--deploy-the-cli)
- [Add an MCP server](#add-an-mcp-server)
- [Deploy on Kubernetes](#deploy-on-kubernetes)
- [Operator mode (24/7 health checks)](#operator-mode-247-health-checks)
- [Data sources](#data-sources)
- [Hacktoberfest 2025 additions](#hacktoberfest-2025-additions)
- [License](#license)

---

## What it does

You ask a question in plain English (*"why is my pod crashlooping?"*).
MavrickGPT runs an **agentic loop**: it calls tools to pull live data from your
cluster, metrics, logs, and APIs, reasons over the results, and returns a root
cause — read-only and RBAC-safe, so it is safe to run in production.

- **Any LLM** — OpenAI, Anthropic, Azure, Bedrock, Gemini, or local open-weight models
- **No Kubernetes required** — works with VMs, bare metal, cloud, or containers
- **Extensible** — add any tool through the Model Context Protocol (MCP)

---

## Install

MavrickGPT uses [Poetry](https://python-poetry.org/). Install it first if you
don't have it (the `command not found: poetry` error means it's missing):

```bash
pipx install poetry            # recommended
# or: curl -sSL https://install.python-poetry.org | python3 -
```

Then clone and install:

```bash
git clone https://github.com/MAVRICK-1/mavrickgpt.git
cd mavrickgpt
poetry install
```

> No Poetry? You can install straight from the repo with pip instead:
> ```bash
> git clone https://github.com/MAVRICK-1/mavrickgpt.git
> cd mavrickgpt && pip install .
> mavrick ask "hello"      # 'mavrick' instead of 'poetry run mavrick'
> ```

---

## Set an LLM key

Any provider works (routed through LiteLLM). Set one:

```bash
export OPENAI_API_KEY="sk-..."       # or ANTHROPIC_API_KEY / GEMINI_API_KEY
```

Open-weight / local models need no key:

```bash
ollama serve
poetry run mavrick ask "hello" --model ollama/llama3.1
```

### Use GitHub Copilot as the LLM (CLI)

Yes — you can drive the CLI with your **GitHub Copilot** subscription instead of
an API key. Copilot uses an OAuth device-flow login (no key to paste), and
MavrickGPT handles the token for you. Just pick a `github_copilot/` model:

```bash
poetry run mavrick ask -i --model github_copilot/gpt-4o
```

The first run prints a one-time code and a URL (https://github.com/login/device).
Enter the code in your browser, authorize once, and the CLI remembers it for
future runs. Other Copilot models work too, e.g.
`github_copilot/claude-sonnet-4` or `github_copilot/o4-mini`.

---

## Run it

```bash
# one-shot question
poetry run mavrick ask "why is my pod crashlooping?"

# interactive chat in the terminal
poetry run mavrick ask -i

# investigate a firing alert
poetry run mavrick investigate alertmanager --alertmanager-url http://localhost:9093
```

Run it as an HTTP API instead:

```bash
poetry run python server.py                 # http://0.0.0.0:5050
curl localhost:5050/healthz                 # -> {"status":"healthy"}
curl localhost:5050/api/chat -H 'Content-Type: application/json' \
  -d '{"ask":"what is wrong with my cluster?"}'
```

The server also exposes an OpenAI-compatible endpoint at `/v1/chat/completions`,
so any OpenAI client or chat UI (e.g. LibreChat) can talk to MavrickGPT.

---

## Build & deploy the CLI

**Build the CLI from scratch** (clean checkout to a working `mavrick` binary):

```bash
# 1. get the code
git clone https://github.com/MAVRICK-1/mavrickgpt.git
cd mavrickgpt

# 2. make sure you have Poetry (skip if you already do)
pipx install poetry

# 3. install all dependencies into an isolated virtualenv
poetry install

# 4. build the installable wheel
poetry build                                  # -> dist/mavrickgpt-*.whl

# 5. install that wheel onto your machine so `mavrick` is on your PATH
pipx install dist/mavrickgpt-*.whl            # or: pip install dist/mavrickgpt-*.whl

# 6. verify
mavrick version
```

Now run it from anywhere:

```bash
mavrick ask "why is my pod crashlooping?"
```

**Build a Docker image** (ships the CLI + HTTP server):

```bash
docker build -t mavrick:local .
docker run --rm -it -e OPENAI_API_KEY="sk-..." mavrick:local \
  ask "why is my pod crashlooping?"
```

**Load the image into a local kind cluster** (for Kubernetes deploys):

```bash
kind create cluster --name mavrick
kind load docker-image mavrick:local --name mavrick
```

Then point the Helm chart at your image and deploy — see
[Deploy on Kubernetes](#deploy-on-kubernetes).

---

## Add an MCP server

MavrickGPT can pull in any external tool through the **Model Context Protocol
(MCP)**. Add servers under `mcp_servers` in `~/.mavrick/config.yaml`.

MavrickGPT connects to MCP servers over HTTP using one of two transports:

- `sse` — Server-Sent Events (URL usually ends in `/sse`)
- `streamable-http` — Streamable HTTP (URL usually ends in `/mcp`)

**Example — add a GitHub MCP server:**

```yaml
# ~/.mavrick/config.yaml
mcp_servers:
  github:
    description: "GitHub MCP Server - repos, issues, and pull requests"
    config:
      url: "http://localhost:8000/sse"
      mode: "sse"
```

**Example — a server that needs an auth header, over streamable-http:**

```yaml
mcp_servers:
  my_api:
    description: "Internal API tools"
    config:
      url: "https://tools.internal.example.com/mcp"
      mode: "streamable-http"
      headers:
        Authorization: "Bearer YOUR_TOKEN"
      verify_ssl: true        # set false for local/dev servers without valid TLS
```

That's it — restart MavrickGPT and the new tools appear automatically. Check
they loaded with:

```bash
poetry run mavrick toolset list
```

### Deploy an MCP server to Kubernetes

In a cluster, run the MCP server as its own Deployment + Service, then point
MavrickGPT at it with the in-cluster DNS name. Here is the **AWS MCP server** so
MavrickGPT can fetch AWS data (RDS events, instances, slow query logs, …):

```yaml
# aws-mcp.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aws-mcp-server
  namespace: mavrick
spec:
  replicas: 1
  selector:
    matchLabels: { app: aws-mcp-server }
  template:
    metadata:
      labels: { app: aws-mcp-server }
    spec:
      containers:
        - name: aws-mcp
          image: ghcr.io/awslabs/mcp/aws-api-mcp-server:latest
          args: ["--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
          ports: [{ containerPort: 8000 }]
          envFrom:
            - secretRef: { name: aws-credentials }   # AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION
---
apiVersion: v1
kind: Service
metadata:
  name: aws-mcp-server
  namespace: mavrick
spec:
  selector: { app: aws-mcp-server }
  ports: [{ port: 8000, targetPort: 8000 }]
```

```bash
# give the MCP server AWS creds, then deploy it
kubectl create secret generic aws-credentials -n mavrick \
  --from-literal=AWS_ACCESS_KEY_ID="..." \
  --from-literal=AWS_SECRET_ACCESS_KEY="..." \
  --from-literal=AWS_REGION="us-east-1"
kubectl apply -f aws-mcp.yaml
```

Then register it with MavrickGPT via the Helm chart's `mcp_servers` config so the
agent connects over in-cluster DNS:

```yaml
# values override for the mavrick chart
additionalConfig:
  mcp_servers:
    aws:
      description: "AWS MCP Server - RDS, EC2, and more"
      config:
        url: "http://aws-mcp-server.mavrick.svc.cluster.local:8000/sse"
        mode: "sse"
```

```bash
helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values -f values-override.yaml
```

Now ask MavrickGPT a question that needs AWS data and it will call the MCP server
to fetch it:

```bash
kubectl exec -n mavrick deploy/mavrick-mavrick -- \
  mavrick ask "list my RDS instances and any recent events"
```

The same pattern works for any MCP server (GitHub, Azure, GitLab, …) — swap the
image and the `url`.

---

## Deploy on Kubernetes

```bash
# install the agent
helm install mavrick ./helm/mavrick -n mavrick --create-namespace

# optional: add the LibreChat web UI
helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values \
  --set librechat.enabled=true
```

Give it an LLM key via a Secret:

```bash
kubectl create secret generic mavrick-llm-keys \
  --from-literal=GEMINI_API_KEY="your-key" -n mavrick

helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values \
  --set 'extraEnvVarsSecrets[0]=mavrick-llm-keys'
```

---

## Operator mode (24/7 health checks)

The operator runs MavrickGPT in the background: it watches health-check CRDs,
investigates on a schedule or on deploy, and reports what it finds. The image is
published to GitHub Container Registry:

```
ghcr.io/mavrick-1/mavrick-operator:0.0.0
```

Enable it in the Helm chart (already pointed at the image above):

```bash
helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values \
  --set operator.enabled=true
```

The operator does not call the LLM directly — it POSTs each check to the main
MavrickGPT API, so it inherits the same model and toolsets.

---

## Data sources

MavrickGPT ships with built-in toolsets for popular platforms. A few of them:

- **Kubernetes** — pod logs, events, and resource status
- **Prometheus** — query metrics and generate PromQL
- **Grafana / Loki / Tempo** — dashboards, logs, and traces
- **Datadog, New Relic, Coralogix** — logs, metrics, and traces
- **AWS, Azure, GCP** — cloud resources and diagnostics
- **PostgreSQL, MySQL, MongoDB** — database queries and diagnostics
- **GitHub, GitLab, Jenkins** — repos, pipelines, and CI/CD
- **Docker, Helm, ArgoCD** — containers, releases, and deployments

Many integrations (GitHub, AWS, Azure, GitLab, Sentry, Splunk, …) are delivered
as MCP servers — see [Add an MCP server](#add-an-mcp-server). You can also add
your own tools through any REST API.

---


---

## License

Distributed under the **Apache 2.0 License** — see [LICENSE](LICENSE).
(Apache 2.0) by Robusta.dev; upstream attribution is retained as required.
