# MavrickGPT — Project Overview 🦾

> **MavrickGPT** is an open-source **AI SRE agent** for investigating production
> incidents and finding root causes. It is a Hacktoberfest 2025 build on top of
> the CNCF sandbox project MavrickGPT — reused as-is and extended with a new
> **tool-call efficiency** signal for the eval judge (see
> [`hackathon/README.md`](./README.md)).
>
> This document explains **everything that is there and what it does**, so you
> can navigate the whole project quickly.

---

## 1. What MavrickGPT is

An LLM-powered agent that troubleshoots infrastructure the way a human SRE does:
it is handed a question or an alert, then **autonomously queries live
observability data** (logs, metrics, traces, Kubernetes state, cloud APIs,
databases, tickets…) through an **agentic tool-calling loop** until it can
explain the root cause.

- Works with **any stack** — Kubernetes, VMs, bare metal, cloud, databases, SaaS.
- **Read-only** by design; respects RBAC. Safe for production.
- **Any LLM provider** — OpenAI, Anthropic, Azure, Bedrock, Gemini, and
  open-weight models via LiteLLM.

## 2. What it does (capabilities)

| Capability | What it means |
| --- | --- |
| **Ask / investigate** | Answer free-form questions or investigate an incoming alert and report the root cause. |
| **Agentic loop** | The LLM repeatedly picks a tool, reads the result, and decides the next step — no fixed script. |
| **Toolsets** | 40+ built-in integrations (Kubernetes, Prometheus, Grafana, Datadog, Loki, AWS, GitHub, SQL DBs, …). |
| **Bidirectional alerts** | Pull alerts from AlertManager / PagerDuty / OpsGenie / Jira and write findings back, or to Slack. |
| **Operator mode** | Runs 24/7 in the background, spots problems early, and can open PRs to fix them. |
| **Memory-safe at scale** | Server-side filtering, output budgeting, and per-tool memory limits keep huge payloads out of the context window. |

## 3. How it works (architecture)

```
        ┌──────────────┐   question / alert
        │  CLI / API   │ ─────────────────────────────┐
        │  / Operator  │                               ▼
        └──────────────┘                     ┌───────────────────────┐
                                             │  Investigation engine │
                                             │  (agentic tool loop)  │
                                             └───────────┬───────────┘
                          pick tool → run → read result │  repeat until solved
                                             ┌───────────▼───────────┐
                                             │       Toolsets        │
                                             │ k8s · Prometheus · …  │
                                             └───────────┬───────────┘
                                                         ▼
                                        live logs / metrics / traces / APIs
```

### Where things live

| Area | Path | Role |
| --- | --- | --- |
| **Core engine** | `mavrick/core/` | `tool_calling_llm.py` (the tool-calling loop), `investigation.py` (multi-step orchestration + runbooks), `toolset_manager.py`, `tools.py` (tool defs + execution). |
| **Plugins** | `mavrick/plugins/` | **Sources** (AlertManager, Jira, PagerDuty…), **Toolsets** (Kubernetes, Prometheus, AWS…), **Prompts** (Jinja2 templates), **Destinations** (Slack). |
| **CLI** | `mavrick/main.py`, `mavrick/interactive.py` | `mavrick ask "…"`, interactive mode. |
| **Server / Operator** | `server.py`, `mavrick_operator/` | HTTP API and the 24/7 Kubernetes operator. |
| **Config** | `mavrick/config.py` | Loads `~/.mavrick/config.yaml`, API keys, model & toolset selection. |
| **Evals** | `tests/llm/` | LLM evaluation harness (fixtures + judge + reporters). |

### Key patterns

- **Toolset = YAML** defining tools (Python functions or safety-validated bash),
  loaded dynamically and customizable via config.
- **Detailed tool errors** are mandatory so the LLM can self-correct.
- **Never return unbounded data** — always filter server-side to avoid token
  overflow.

## 4. The Hacktoberfest contribution — Tool Call Efficiency

Evals historically scored only **correctness**. Small open-weight models can be
"correct" yet wasteful — repeating near-identical calls or retrying an identical
failing call. This contribution adds an **advisory efficiency metric** computed
from the recorded trajectory (no extra LLM call, never fails a test):

- `total_tool_calls`, `duplicate_calls`, `retry_loops`
- `efficiency_score = min(1, expected/actual) × (1 − duplicates/total)`
- opt-in per eval via `expected_tool_calls: <int>` in `test_case.yaml`
- reported next to correctness in the terminal **and** GitHub reports.

**Files:** `tests/llm/utils/tool_call_efficiency.py` (+ tests),
`tests/llm/utils/test_case_utils.py`, `tests/llm/test_ask_mavrick.py`,
`tests/llm/utils/reporting/{terminal,github}_reporter.py`.

See [`hackathon/README.md`](./README.md) for the full feature writeup.

## 5. Try it now

```bash
# 1) Offline efficiency demo (no API key, no Kubernetes)
python hackathon/mavrick_efficiency_demo.py

# 2) Unit tests for the new metric
poetry run pytest tests/llm/utils/test_tool_call_efficiency.py -q   # 10 passed

# 3) Use the agent itself (needs an LLM API key)
poetry install --with dev
export OPENAI_API_KEY="…"          # or ANTHROPIC_API_KEY, etc.
poetry run mavrick ask "what is wrong with my cluster?"
```

## 6. License & credits

Reuses **MavrickGPT** (Apache 2.0), a CNCF sandbox project originally created by
[Robusta.dev](https://robusta.dev) with major contributions from Microsoft.
MavrickGPT is a Hacktoberfest rebrand + feature contribution; all upstream
attribution and links are preserved.
