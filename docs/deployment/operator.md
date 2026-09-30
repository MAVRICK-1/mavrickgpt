# MavrickGPT Operator (24/7 proactive mode)

The **operator** runs MavrickGPT continuously inside your cluster. Instead of
waiting for a human to ask a question, it executes **scheduled health checks**,
investigates issues with the same agentic tool loop, and alerts you (Slack,
PagerDuty, …) when something looks wrong.

---

## 1. How it works

```
   ScheduledHealthCheck CR ──▶ Operator ──▶ MavrickGPT API (/api/chat) ──▶ toolsets
        (cron + prompt)            │                                          │
                                   ▼                                          ▼
                          TriggeredHealthCheck CR  ◀── investigates ── live cluster data
                                   │
                                   ▼
                      alert on failure (Slack / PagerDuty / ...)
```

- The operator watches three CRDs (installed by the Helm chart under `crds/`):
  - **`HealthCheck`** — a health check definition
  - **`ScheduledHealthCheck`** — a check that runs on a cron schedule
  - **`TriggeredHealthCheck`** — a single run/record of a check
- On each tick it asks MavrickGPT a **natural-language health question**; the
  agent investigates using its toolsets and returns a verdict.
- Source: `mavrick_operator/` (handlers `scheduledhealthcheck`, `healthcheck`,
  `triggeredhealthcheck`).

---

## 2. Enable the operator

The operator ships with the main chart, disabled by default:

```bash
helm upgrade mavrick ./helm/mavrick -n mavrick --reuse-values \
  --set operator.enabled=true

kubectl -n mavrick rollout status deploy/mavrick-operator
```

Key `values.yaml` settings (under `operator:`):

| Value | Default | Purpose |
| --- | --- | --- |
| `operator.enabled` | `false` | Deploy the operator |
| `operator.mavrickApiUrl` | `http://<release>-mavrick:80` | Agent API it calls |
| `operator.mavrickApiTimeout` | `300` | Per-check timeout (s) |
| `operator.logLevel` | `INFO` | Operator log level |
| `operator.cleanupCompletedChecks` | `false` | GC finished check records |

---

## 3. Define a scheduled health check

Create a `ScheduledHealthCheck` resource:

```yaml
apiVersion: mavrickgpt.dev/v1
kind: ScheduledHealthCheck
metadata:
  name: checkout-latency
  namespace: mavrick
spec:
  schedule: "*/5 * * * *"          # every 5 minutes (cron)
  enabled: true
  prompt: "Is the checkout service healthy? Check error rate and p95 latency."
  mode: alert                       # 'alert' notifies on failure, 'monitor' just logs
  timeout: 300
  # model: gpt-4o                   # optional per-check model override
  destinations:                     # only used in 'alert' mode
    - type: slack
      # ...destination-specific fields
```

Apply and inspect:

```bash
kubectl apply -f checkout-latency.yaml
kubectl -n mavrick get scheduledhealthchecks
kubectl -n mavrick get triggeredhealthchecks   # individual runs appear here
kubectl -n mavrick logs deploy/mavrick-operator
```

### Fields (from the CRD schema)

| Field | Type | Meaning |
| --- | --- | --- |
| `schedule` | string (cron) | When to run, e.g. `*/5 * * * *` (required) |
| `enabled` | bool | Toggle the schedule |
| `prompt` | string | Natural-language health question |
| `timeout` | int | Execution timeout in seconds |
| `mode` | `alert` \| `monitor` | Notify on failure vs log only |
| `model` | string | Override the default LLM for this check |
| `destinations[]` | list | Alert targets (e.g. `slack`, `pagerduty`) in `alert` mode |

---

## 4. Typical uses

- **Deployment verification** — after a rollout, a check confirms the new
  version is healthy.
- **Golden-signal monitoring** — periodic checks on latency/error budgets that
  investigate *why* before paging you.
- **Proactive triage** — the agent notices a problem and posts a root-cause
  summary to Slack before customers notice.

See also: [Kubernetes deployment guide](./kubernetes-deployment.md).
