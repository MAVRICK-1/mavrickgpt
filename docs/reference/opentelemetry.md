# OpenTelemetry Observability

MavrickGPT includes built-in OpenTelemetry (OTel) instrumentation that produces **distributed traces** and **metrics** for every investigation. This enables end-to-end observability from user prompt through LLM calls and MCP tool execution.

## Enabling OpenTelemetry

OTel instrumentation activates automatically when the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable is set. No code changes or flags are needed.

### CLI

```bash
# Run with OTel enabled
export OTEL_EXPORTER_OTLP_ENDPOINT="http://your-otel-collector:4317"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
export OTEL_SERVICE_NAME="mavrickgpt"
mavrick ask "Why is my pod crashing?"
```

### Helm / Kubernetes

Add the following to your Helm `values.yaml`:

```yaml
additionalEnvVars:
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://otel-collector.monitoring.svc:4317"
  - name: OTEL_EXPORTER_OTLP_PROTOCOL
    value: "grpc"
  - name: OTEL_SERVICE_NAME
    value: "mavrickgpt"
  # Optional: for backends requiring auth (e.g., Dynatrace, Grafana Cloud)
  - name: OTEL_EXPORTER_OTLP_HEADERS
    value: "Authorization=Api-Token YOUR_TOKEN"
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint (enables OTel when set) | *(unset — OTel disabled)* |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Export protocol (`grpc` or `http/protobuf`) | `grpc` |
| `OTEL_SERVICE_NAME` | Service name in traces/metrics | `mavrickgpt` |
| `OTEL_EXPORTER_OTLP_HEADERS` | Headers for OTLP exporter (e.g., auth tokens) | *(none)* |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` | Override metrics endpoint (if different from traces) | *(uses OTEL_EXPORTER_OTLP_ENDPOINT)* |
| `MAVRICK_LANGFUSE_ATTRIBUTES` | Emit Langfuse-specific span attributes (prompts, tool I/O, thinking, user/session, tags). See [Langfuse](#langfuse). | `false` |
| `MAVRICK_OTEL_MAX_ATTR_CHARS` | Max characters for the input/output attributes emitted when `MAVRICK_LANGFUSE_ATTRIBUTES` is enabled | `100000` |

When `OTEL_EXPORTER_OTLP_ENDPOINT` is **not** set, MavrickGPT uses a no-op `DummyTracer` with zero overhead.

## Distributed Traces

Every investigation produces a trace hierarchy:

```
mavrickgpt.investigation (root span)
├── gen_ai.chat (LLM iteration 0 — includes token counts)
│   └── POST (auto-instrumented httpx → LLM provider)
├── mavrickgpt.tool.<name> (tool/MCP call)
│   └── POST (auto-instrumented httpx → MCP server)
│       └── MCP server spans (execute_tool, k8s.api/*, etc.)
├── gen_ai.chat (LLM iteration 1)
│   └── ...
└── gen_ai.chat (final iteration — produces answer)
```

### Span Attributes

**Investigation span** (`mavrickgpt.investigation`):
- `mavrickgpt.investigation.question` — the user's question
- `mavrickgpt.investigation.stream` — whether streaming was used

**LLM spans** (`gen_ai.chat`):
- `gen_ai.system` — LLM provider (`litellm`)
- `gen_ai.request.model` — model name
- `gen_ai.usage.input_tokens` — prompt tokens
- `gen_ai.usage.output_tokens` — completion tokens
- `gen_ai.usage.total_tokens` — total tokens
- `mavrickgpt.iteration` — iteration number (0-based)

**Tool spans** (`mavrickgpt.tool.<name>`):
- `mavrickgpt.tool.name` — tool name
- `mavrickgpt.tool.status` — result status (`success` or `error`)

### MCP Trace Propagation

When MavrickGPT calls MCP tools over HTTP, trace context is automatically propagated via W3C `traceparent` headers (using httpx auto-instrumentation). MCP servers that support OpenTelemetry will create child spans linked to the same trace.

## Metrics

MavrickGPT exports the following OTel metrics via OTLP. All metrics use **underscore-delimited attribute keys** for maximum compatibility across backends.

### Token Usage

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `gen_ai.client.token.usage` | Counter | `{token}` | LLM token consumption |

**Dimensions:** `gen_ai_request_model`, `gen_ai_system`, `gen_ai_token_type` (`input` or `output`)

### Investigation Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `mavrickgpt.investigation.count` | Counter | `{investigation}` | Number of investigations started |
| `mavrickgpt.investigation.duration` | Histogram | `s` | End-to-end investigation duration |
| `mavrickgpt.investigation.iterations` | Histogram | `{iteration}` | LLM iterations per investigation |

**Dimensions:** `gen_ai_request_model`

### LLM Call Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `gen_ai.client.operation.duration` | Histogram | `s` | Individual LLM call latency |

**Dimensions:** `gen_ai_request_model`, `gen_ai_system`

### Tool / MCP Call Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `mavrickgpt.tool.call.count` | Counter | `{call}` | Number of tool calls |
| `mavrickgpt.tool.call.duration` | Histogram | `s` | Tool call latency |
| `mavrickgpt.tool.call.errors` | Counter | `{error}` | Failed tool calls |

**Dimensions:** `mavrickgpt_tool_name`

### Example Queries

**Dynatrace DQL:**

```sql
# Tool call duration by tool name
timeseries avg(mavrickgpt.tool.call.duration, default:0), by: {mavrickgpt_tool_name}

# Token usage by model
timeseries sum(gen_ai.client.token.usage, default:0), by: {gen_ai_request_model, gen_ai_token_type}

# Investigation count over time
timeseries sum(mavrickgpt.investigation.count, default:0)

# Slowest tools (p95)
timeseries percentile(mavrickgpt.tool.call.duration, 95), by: {mavrickgpt_tool_name}
```

**PromQL (Grafana / Prometheus):**

```promql
# Tool call rate by tool name
rate(mavrickgpt_tool_call_count_total[5m])

# Average LLM call duration
rate(gen_ai_client_operation_duration_sum[5m]) / rate(gen_ai_client_operation_duration_count[5m])
```

## Backend Examples

### Dynatrace (direct OTLP)

```yaml
additionalEnvVars:
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "https://YOUR_ENV.live.dynatrace.com/api/v2/otlp"
  - name: OTEL_EXPORTER_OTLP_PROTOCOL
    value: "grpc"
  - name: OTEL_SERVICE_NAME
    value: "mavrickgpt"
  - name: OTEL_EXPORTER_OTLP_HEADERS
    value: "Authorization=Api-Token YOUR_DT_TOKEN"
```

### OTel Collector (self-hosted)

```yaml
additionalEnvVars:
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://otel-collector.monitoring.svc:4317"
  - name: OTEL_EXPORTER_OTLP_PROTOCOL
    value: "grpc"
  - name: OTEL_SERVICE_NAME
    value: "mavrickgpt"
```

### Grafana Cloud

```yaml
additionalEnvVars:
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "https://otlp-gateway-prod-us-east-0.grafana.net/otlp"
  - name: OTEL_EXPORTER_OTLP_PROTOCOL
    value: "grpc"
  - name: OTEL_SERVICE_NAME
    value: "mavrickgpt"
  - name: OTEL_EXPORTER_OTLP_HEADERS
    value: "Authorization=Basic BASE64_ENCODED_INSTANCE:TOKEN"
```

### Langfuse

[Langfuse](https://langfuse.com/) is an LLM-observability platform that ingests OpenTelemetry traces natively. MavrickGPT can export each investigation to Langfuse as a full audit trail — the initiating user, the prompts sent to the LLM, the model's thinking/reasoning, the tools it called with their arguments and outputs, and the final answer.

**Two things are required:**

1. Point the OTLP exporter at your Langfuse project's OTLP endpoint over **HTTP** (Langfuse does not support gRPC), authenticated with a Basic-auth header of `base64(<public-key>:<secret-key>)`.
2. Set **`MAVRICK_LANGFUSE_ATTRIBUTES=true`**. This is opt-in and **off by default** because it emits Langfuse-vendor-specific span attributes (`langfuse.*`) that would be noise for a generic OTel backend. Without it, Mavrick exports only vendor-neutral OTel/`gen_ai.*` spans and the Langfuse Input/Output panels stay empty.

Generate the Basic-auth value:

```bash
echo -n "pk-lf-xxxx:sk-lf-xxxx" | base64
```

=== "Mavrick CLI"

    ```bash
    export OTEL_EXPORTER_OTLP_ENDPOINT="https://cloud.langfuse.com/api/public/otel"
    export OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
    export OTEL_SERVICE_NAME="mavrickgpt"
    export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic <base64(public:secret)>"
    export MAVRICK_LANGFUSE_ATTRIBUTES="true"
    mavrick ask "Why is my pod crashing?"
    ```

=== "Helm / Kubernetes"

    Store the Basic-auth value in a secret, then:

    ```yaml
    additionalEnvVars:
      - name: OTEL_EXPORTER_OTLP_ENDPOINT
        value: "https://cloud.langfuse.com/api/public/otel"  # or your EU / self-hosted host
      - name: OTEL_EXPORTER_OTLP_PROTOCOL
        value: "http/protobuf"
      - name: OTEL_SERVICE_NAME
        value: "mavrickgpt"
      - name: MAVRICK_LANGFUSE_ATTRIBUTES
        value: "true"
      - name: OTEL_EXPORTER_OTLP_HEADERS
        valueFrom:
          secretKeyRef:
            name: mavrick-langfuse-otlp
            key: OTEL_EXPORTER_OTLP_HEADERS   # value: "Authorization=Basic <base64(public:secret)>"
    ```

**What `MAVRICK_LANGFUSE_ATTRIBUTES=true` adds** (all under the `langfuse.*` namespace):

- **Trace-level input/output** — the user's question (input) and Mavrick's final answer (output) on the `mavrickgpt.investigation` root, so the top of the trace shows the prompt and the answer at a glance.
- **Observation input/output** — the prompt messages, the assistant's response, its `reasoning` (thinking), and the tool calls it chose (on `gen_ai.chat` spans); tool arguments and results (on `mavrickgpt.tool.*` spans).
- **Trace user & session** — `langfuse.user.id` (initiating user, falling back through user id → email → account id) and `langfuse.session.id` (the conversation id), powering Langfuse's Users and Sessions views.
- **Trace tags** — `source:<request_source>`, `cluster:<cluster>`, `model:<model>`.
- **Filterable trace metadata** — `user_id`, `user_email`, `conversation_id`, `account_id`, `cluster_id`, `model`, `request_source`.

Since Mavrick emits OTel **metrics** as well and Langfuse ingests **traces only**, metric exports to the Langfuse endpoint are rejected harmlessly (traces are unaffected). To avoid that noise entirely, route Mavrick through an OTel Collector and forward only traces to Langfuse.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    MavrickGPT                         │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Tracer   │  │  Metrics  │  │ httpx auto-instr │   │
│  │ (traces)  │  │(counters, │  │ (W3C traceparent)│   │
│  │          │  │histograms)│  │                  │   │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│       │              │                 │             │
└───────┼──────────────┼─────────────────┼─────────────┘
        │              │                 │
        │ OTLP (gRPC or│                 │ W3C traceparent
        │ HTTP/protobuf)│                │
        ▼              ▼                 ▼
┌─────────────────┐              ┌─────────────────┐
│  OTel Collector  │              │   MCP Servers    │
│  or Direct OTLP  │              │  (child spans)   │
└────────┬────────┘              └─────────────────┘
         │
         ▼
┌─────────────────┐
│    Backend       │
│ (Dynatrace,     │
│  Grafana, etc.) │
└─────────────────┘
```
