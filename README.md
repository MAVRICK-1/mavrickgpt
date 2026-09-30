<div align="center">
  <h1 align="center">MavrickGPT — The CNCF SRE Agent</h1>

  <p align="center">
    <a href="#installation"><strong>Installation</strong></a> |
    <a href="https://mavrickgpt.dev/"><strong>Docs</strong></a> |
    <a href="https://deepwiki.com/MavrickGPT/mavrickgpt"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
  </p>
</div>

Open-source AI agent for investigating production incidents and finding root causes. Works with any stack — Kubernetes, VMs, cloud providers, databases, and SaaS platforms. We are a [Cloud Native Computing Foundation](https://www.cncf.io/) sandbox project. Originally created by [Robusta.Dev](http://robusta.dev), with major contributions from [Microsoft](https://microsoft.com/).

## New: Operator Mode — Find Problems 24/7 in the Background

Most AI agents are great at troubleshooting problems, but still need a human to notice something is wrong and trigger an investigation. [Operator mode](https://mavrickgpt.dev/operator/) fixes that — MavrickGPT runs in the background 24/7, spots problems before your customers notice, and messages you in Slack with the fix. Connect the [GitHub integration](https://mavrickgpt.dev/data-sources/builtin-toolsets/github-mcp/) and it can even open PRs to fix what it finds.

While the operator itself runs in Kubernetes, health checks can query any data source MavrickGPT is connected to — VMs, cloud services, databases, SaaS platforms, and more.

- **[Deployment verification](https://mavrickgpt.dev/operator/deployment-verification/)** — Deploy a health check alongside your app to verify the new version is healthy
- **[Scheduled health checks](https://mavrickgpt.dev/operator/scheduled-health-checks/)** — Continuously monitor services and catch regressions automatically

## Features

- **Petabyte-scale data**: Server-side filtering, JSON tree traversal, and tool output transformers keep large payloads out of context windows
- **Memory-safe execution**: Per-tool memory limits, streaming large results to disk, and automatic output budgeting prevent OOM kills when querying large observability datasets
- **[Deep integrations](https://mavrickgpt.dev/data-sources/builtin-toolsets/)**: Prometheus, Grafana, Datadog, Kubernetes, and [many more](#-data-sources)—plus any [REST API](https://mavrickgpt.dev/data-sources/api-toolsets/)
- **Bidirectional alert integrations**: Fetch alerts from AlertManager, PagerDuty, OpsGenie, or Jira—and write findings back
- **[Any LLM provider](https://mavrickgpt.dev/ai-providers/)**: OpenAI, Anthropic, Azure, Bedrock, Gemini, and more
- **No Kubernetes required**: Works with any infrastructure — VMs, bare metal, cloud services, or containers

## How it Works

MavrickGPT uses an **agentic loop** to query live observability data from multiple sources and identify root causes.

<img width="3114" alt="mavrickgpt-architecture-diagram" src="https://github.com/user-attachments/assets/f659707e-1958-4add-9238-8565a5e3713a" />

![MavrickGPT Investigation Demo](https://mavrickgpt.dev/assets/MavrickInvestigation.gif)

### 🔗 Data Sources

MavrickGPT integrates with popular observability and cloud platforms. The following data sources ("toolsets") are built-in. [Add your own](https://mavrickgpt.dev/data-sources/custom-toolsets/).

| Data Source | Notes |
|-------------|-------|
| [<img src="images/integration_logos/aks-icon.png" alt="AKS" width="20" style="vertical-align: middle;"> **AKS**](https://mavrickgpt.dev/data-sources/builtin-toolsets/aks/) | Azure Kubernetes Service cluster and node health diagnostics |
| [<img src="images/integration_logos/jira-icon.png" alt="Atlassian Rovo" width="20" style="vertical-align: middle;"> **Atlassian Rovo**](https://mavrickgpt.dev/data-sources/builtin-toolsets/atlassian-rovo-mcp/) | Jira issues and Confluence pages via Atlassian's hosted server (MCP) |
| [<img src="images/integration_logos/argocd-icon.png" alt="ArgoCD" width="20" style="vertical-align: middle;"> **ArgoCD**](https://mavrickgpt.dev/data-sources/builtin-toolsets/argocd/) | Get status, history and manifests and more of apps, projects and clusters |
| [<img src="images/integration_logos/aws_logo.png" alt="AWS" width="20" style="vertical-align: middle;"> **AWS**](https://mavrickgpt.dev/data-sources/builtin-toolsets/aws/) | RDS events, instances, slow query logs, and more (MCP) |
| [<img src="images/integration_logos/azure.png" alt="Azure" width="20" style="vertical-align: middle;"> **Azure**](https://mavrickgpt.dev/data-sources/builtin-toolsets/azure-mcp/) | Azure resources and diagnostics (MCP) |
| [<img src="images/integration_logos/confluence_logo.png" alt="Confluence" width="20" style="vertical-align: middle;"> **Confluence**](https://mavrickgpt.dev/data-sources/builtin-toolsets/confluence/) | Private runbooks and documentation |
| [<img src="images/integration_logos/confluence_logo.png" alt="Confluence MCP" width="20" style="vertical-align: middle;"> **Confluence (MCP)**](https://mavrickgpt.dev/data-sources/builtin-toolsets/confluence-mcp/) | Private runbooks and documentation (MCP) |
| [<img src="images/integration_logos/coralogix-icon.png" alt="Coralogix" width="20" style="vertical-align: middle;"> **Coralogix**](https://mavrickgpt.dev/data-sources/builtin-toolsets/coralogix-logs/) | Retrieve logs for any resource |
| [<img src="images/integration_logos/crossplane-icon.png" alt="Crossplane" width="20" style="vertical-align: middle;"> **Crossplane**](https://mavrickgpt.dev/data-sources/builtin-toolsets/crossplane/) | Troubleshoot Crossplane providers, compositions, claims, and managed resources |
| [<img src="images/integration_logos/datadog_logo.png" alt="Datadog" width="20" style="vertical-align: middle;"> **Datadog**](https://mavrickgpt.dev/data-sources/builtin-toolsets/datadog/) | Query logs, metrics, and traces |
| [<img src="images/integration_logos/docker_logo.png" alt="Docker" width="20" style="vertical-align: middle;"> **Docker**](https://mavrickgpt.dev/data-sources/builtin-toolsets/docker/) | Get images, logs, events, history and more |
| [<img src="images/integration_logos/opensearchserverless-icon.png" alt="Elasticsearch" width="20" style="vertical-align: middle;"> **Elasticsearch / OpenSearch**](https://mavrickgpt.dev/data-sources/builtin-toolsets/elasticsearch/) | Query logs, cluster health, shard and index diagnostics |
| [<img src="images/integration_logos/gcpmonitoring-icon.png" alt="GCP" width="20" style="vertical-align: middle;"> **GCP**](https://mavrickgpt.dev/data-sources/builtin-toolsets/gcp/) | Google Cloud Platform resources (MCP) |
| [<img src="images/integration_logos/github_logo.png" alt="GitHub" width="20" style="vertical-align: middle;"> **GitHub**](https://mavrickgpt.dev/data-sources/builtin-toolsets/github-mcp/) | Repositories, issues, and pull requests (MCP) |
| [<img src="images/integration_logos/gitlab-icon.png" alt="GitLab" width="20" style="vertical-align: middle;"> **GitLab**](https://mavrickgpt.dev/data-sources/builtin-toolsets/gitlab-mcp/) | Projects, merge requests, issues, and CI/CD pipelines (MCP) |
| [<img src="images/integration_logos/jenkins-icon.png" alt="Jenkins" width="20" style="vertical-align: middle;"> **Jenkins (MCP)**](https://mavrickgpt.dev/data-sources/builtin-toolsets/jenkins-mcp/) | Build status, pipeline logs, and job history (MCP) |
| [<img src="images/integration_logos/grafana-icon.png" alt="Grafana" width="20" style="vertical-align: middle;"> **Grafana**](https://mavrickgpt.dev/data-sources/builtin-toolsets/grafanadashboards/) | Query and analyze dashboard configurations and panels |
| [<img src="images/integration_logos/helm_logo.png" alt="Helm" width="20" style="vertical-align: middle;"> **Helm**](https://mavrickgpt.dev/data-sources/builtin-toolsets/helm/) | Release status, chart metadata, and values |
| [<img src="images/integration_logos/http-icon.png" alt="Internet" width="20" style="vertical-align: middle;"> **Internet**](https://mavrickgpt.dev/data-sources/builtin-toolsets/internet/) | Public runbooks, community docs, etc. |
| [<img src="images/integration_logos/kafka_logo.png" alt="Kafka" width="20" style="vertical-align: middle;"> **Kafka**](https://mavrickgpt.dev/data-sources/builtin-toolsets/kafka/) | Fetch metadata, list consumers and topics or find lagging consumer groups |
| [<img src="images/integration_logos/kubernetes-icon.png" alt="Kubernetes" width="20" style="vertical-align: middle;"> **Kubernetes**](https://mavrickgpt.dev/data-sources/builtin-toolsets/kubernetes/) | Pod logs, K8s events, and resource status (kubectl describe) |
| [<img src="images/integration_logos/kubernetes-icon.png" alt="Kubernetes Remediation" width="20" style="vertical-align: middle;"> **Kubernetes Remediation (MCP)**](https://mavrickgpt.dev/data-sources/builtin-toolsets/kubernetes-remediation-mcp/) | Apply fixes like scaling, rollbacks, and resource edits (MCP) |
| [<img src="images/integration_logos/grafana_loki-icon.png" alt="Loki" width="20" style="vertical-align: middle;"> **Loki**](https://mavrickgpt.dev/data-sources/builtin-toolsets/grafanaloki/) | Query logs for Kubernetes resources or any query |
| [<img src="images/integration_logos/postgres-icon.png" alt="MariaDB" width="20" style="vertical-align: middle;"> **MariaDB**](https://mavrickgpt.dev/data-sources/builtin-toolsets/database-mariadb/) | MariaDB database queries and diagnostics |
| [<img src="images/integration_logos/postgres-icon.png" alt="MongoDB" width="20" style="vertical-align: middle;"> **MongoDB**](https://mavrickgpt.dev/data-sources/builtin-toolsets/mongodb/) | Query data, diagnose performance, inspect schemas, find slow operations |
| [<img src="images/integration_logos/postgres-icon.png" alt="MongoDB Atlas" width="20" style="vertical-align: middle;"> **MongoDB Atlas**](https://mavrickgpt.dev/data-sources/builtin-toolsets/mongodb-atlas/) | Cluster health, slow queries, and performance diagnostics |
| [<img src="images/integration_logos/newrelic_logo.png" alt="NewRelic" width="20" style="vertical-align: middle;"> **NewRelic**](https://mavrickgpt.dev/data-sources/builtin-toolsets/newrelic/) | Investigate alerts, query tracing data |
| [<img src="images/integration_logos/openshift-icon.png" alt="OpenShift" width="20" style="vertical-align: middle;"> **OpenShift**](https://mavrickgpt.dev/data-sources/builtin-toolsets/openshift/) | Projects, routes, builds, security context constraints, and deployment configs |
| [<img src="images/integration_logos/prefect-icon.png" alt="Prefect" width="20" style="vertical-align: middle;"> **Prefect (MCP)**](https://mavrickgpt.dev/data-sources/builtin-toolsets/prefect-mcp/) | Workflow orchestration monitoring, flow runs, and worker health (MCP) |
| [<img src="images/integration_logos/prometheus-icon.png" alt="Prometheus" width="20" style="vertical-align: middle;"> **Prometheus**](https://mavrickgpt.dev/data-sources/builtin-toolsets/prometheus/) | Investigate alerts, query metrics and generate PromQL queries |
| [<img src="images/integration_logos/rabbit_mq_logo.png" alt="RabbitMQ" width="20" style="vertical-align: middle;"> **RabbitMQ**](https://mavrickgpt.dev/data-sources/builtin-toolsets/rabbitmq/) | Partitions, memory/disk alerts, troubleshoot split-brain scenarios and more |
| [<img src="images/integration_logos/robusta_logo.png" alt="Robusta" width="20" style="vertical-align: middle;"> **Robusta**](https://mavrickgpt.dev/data-sources/builtin-toolsets/robusta/) | Multi-cluster monitoring, historical change data, runbooks, PromQL graphs and more |
| [<img src="images/integration_logos/servicenow-icon.png" alt="ServiceNow" width="20" style="vertical-align: middle;"> **ServiceNow**](https://mavrickgpt.dev/data-sources/builtin-toolsets/servicenow/) | Query tables and incident records |
| [<img src="images/integration_logos/sentry-icon.png" alt="Sentry" width="20" style="vertical-align: middle;"> **Sentry**](https://mavrickgpt.dev/data-sources/builtin-toolsets/sentry-mcp/) | Error tracking, issues, and performance monitoring (MCP) |
| [<img src="images/integration_logos/slab_logo.png" alt="Slab" width="20" style="vertical-align: middle;"> **Slab**](https://mavrickgpt.dev/data-sources/builtin-toolsets/slab/) | Team knowledge base and runbooks on demand |
| **Splunk** | Log search and analysis (MCP) |
| [<img src="images/integration_logos/postgres-icon.png" alt="SQL Databases" width="20" style="vertical-align: middle;"> **SQL Databases**](https://mavrickgpt.dev/data-sources/builtin-toolsets/database-postgresql/) | PostgreSQL, MySQL, ClickHouse, MariaDB, SQL Server, Azure SQL, SQLite |
| [<img src="images/integration_logos/tempo_logo.png" alt="Tempo" width="20" style="vertical-align: middle;"> **Tempo**](https://mavrickgpt.dev/data-sources/builtin-toolsets/grafanatempo/) | Fetch trace info, debug issues like high latency in application |
| [<img src="images/integration_logos/victorialogs-icon.png" alt="VictoriaLogs" width="20" style="vertical-align: middle;"> **VictoriaLogs**](https://mavrickgpt.dev/data-sources/builtin-toolsets/victorialogs/) | Query logs from VictoriaLogs using LogsQL |
| **VictoriaMetrics** | Query metrics from a Prometheus-compatible TSDB (`vmsingle` / `vmcluster`) |
| [<img src="images/integration_logos/zabbix-icon.png" alt="Zabbix" width="20" style="vertical-align: middle;"> **Zabbix**](https://mavrickgpt.dev/data-sources/builtin-toolsets/zabbix/) | Monitor hosts, problems, events, triggers, and historical metrics |

See the [full list of built-in toolsets](https://mavrickgpt.dev/data-sources/builtin-toolsets/) for additional integrations including Cilium, KubeVela, Notion, and more.

### 🚀 End-to-End Automation

MavrickGPT can fetch alerts/tickets to investigate from external systems, then write the analysis back to the source or Slack.

| Integration             | Status    | Notes |
|-------------------------|-----------|-------|
| Slack                   | ✅        | [Demo.](https://www.loom.com/share/afcd81444b1a4adfaa0bbe01c37a4847) Available via [Robusta](https://home.robusta.dev/) |
| Microsoft Teams         | ✅        | Available via [Robusta](https://home.robusta.dev/) |
| Prometheus/AlertManager | ✅        | Robusta or MavrickGPT CLI |
| PagerDuty               | ✅        | MavrickGPT CLI only |
| OpsGenie                | ✅        | MavrickGPT CLI only |
| Jira                    | ✅        | MavrickGPT CLI only |
| GitHub                  | ✅        | MavrickGPT CLI only |

## Installation

<a href="https://mavrickgpt.dev/installation/cli-installation/">
  <img src="images/integration_logos/all-installation-methods.png" alt="All Installation Methods" style="max-width:100%; height:auto;">
</a>

Read the [installation documentation](https://mavrickgpt.dev/installation/cli-installation/) to learn how to install MavrickGPT.

## How to Run

### 1. Install from source (Poetry)

```bash
git clone https://github.com/MAVRICK-1/mavrickgpt.git
cd mavrickgpt
poetry install
```

### 2. Set an LLM API key

Any provider works (routed via LiteLLM). Set one:

```bash
export OPENAI_API_KEY="sk-..."      # or ANTHROPIC_API_KEY / GEMINI_API_KEY
# open-weight / local models need no key:  ollama serve  then  --model ollama/llama3.1
```

### 3. Ask a question (CLI)

```bash
# one-shot
poetry run mavrick ask "why is my pod crashlooping?"

# interactive chat in the terminal
poetry run mavrick ask -i

# investigate a firing alert / ticket
poetry run mavrick investigate alertmanager --alertmanager-url http://localhost:9093
```

Other subcommands: `mavrick toolset list`, `mavrick checks`, `mavrick version`.

### 4. Run the HTTP API server

```bash
poetry run python server.py          # serves on http://0.0.0.0:5050
curl localhost:5050/healthz          # -> {"status":"healthy"}
curl localhost:5050/api/chat -H 'Content-Type: application/json' \
  -d '{"ask":"what is wrong with my cluster?"}'
```

### 5. Run in Docker

```bash
docker build -t mavrick:local .
docker run --rm -p 5050:5050 -e OPENAI_API_KEY="sk-..." mavrick:local
```

### 6. Run on Kubernetes

See [Deploy on Kubernetes](#-deploy-on-kubernetes) below (Helm + optional LibreChat UI).

## Supported LLM Providers

<a href="https://mavrickgpt.dev/ai-providers/">
  <img src="images/integration_logos/all-integration-providers.png" alt="All Integration Providers" style="max-width:100%; height:auto;">
</a>

Read the [LLM Providers documentation](https://mavrickgpt.dev/ai-providers/) to learn how to set up your LLM API key.

## Using MavrickGPT

See the [walkthrough documentation](https://mavrickgpt.dev/latest/walkthrough/) for usage guides, including:

- [Interactive mode](https://mavrickgpt.dev/latest/walkthrough/interactive-mode/) for asking questions and follow-ups
- [Investigating Prometheus alerts](https://mavrickgpt.dev/latest/walkthrough/investigating-prometheus-alerts/)
- [CI/CD troubleshooting](https://mavrickgpt.dev/latest/walkthrough/cicd-troubleshooting/)

## 🔐 Data Privacy

By design, MavrickGPT has **read-only access** and respects RBAC permissions. It is safe to run in production environments.

## 🏆 Hacktoberfest 2025 additions

This fork (theme: **open-source AI / open-weight models**) adds:

- **Tool-call efficiency metric** for the eval judge — flags wasted, duplicate, and retry-loop tool calls (common on small open-weight models). Advisory and opt-in; never fails a test. See [`hackathon/`](hackathon/).
- **LibreChat web UI** + Helm chart (opt-in) — an open-source chat interface for MavrickGPT.
- **Kubernetes deployment & operator docs** — see [`docs/deployment/`](docs/deployment/README.md).

## 🚀 Deploy on Kubernetes

```bash
helm install mavrick ./helm/mavrick -n mavrick --create-namespace
# optional web UI:
helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values --set librechat.enabled=true
```

Full guide (deploy to a cluster, web UI, operator):
[docs/deployment/README.md](docs/deployment/README.md)

## License

Distributed under the **Apache 2.0 License** — see [LICENSE](LICENSE). MavrickGPT is
built on [HolmesGPT](https://github.com/robusta-dev/holmesgpt) (Apache 2.0) by
Robusta.dev; upstream attribution is retained as required by the license.
