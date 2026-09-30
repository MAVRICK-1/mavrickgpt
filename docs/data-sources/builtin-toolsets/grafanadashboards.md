# Grafana Dashboards

Connect MavrickGPT to Grafana for dashboard analysis, visual rendering, query extraction, and understanding your monitoring setup. When the [Grafana Image Renderer](https://grafana.com/grafana/plugins/grafana-image-renderer/) is installed, MavrickGPT can visually render dashboards and panels to detect anomalies like spikes, trends, and outliers.

## Prerequisites

A [Grafana service account token](https://grafana.com/docs/grafana/latest/administration/service-accounts/) with the following permissions:

- Basic role → Viewer

For visual rendering, the [Grafana Image Renderer](https://grafana.com/grafana/plugins/grafana-image-renderer/) plugin must be installed on your Grafana instance and `enable_rendering: true` must be set in the config. MavrickGPT auto-detects the renderer — if it's not installed, visual rendering tools are simply not registered and everything else works normally.

## Configuration

=== "Mavrick CLI"

    Add the following to **~/.mavrick/config.yaml**. Create the file if it doesn't exist:

    ```yaml
    toolsets:
      grafana/dashboards:
        enabled: true
        config:
          api_key: <your grafana service account token>
          api_url: <your grafana url>  # e.g. https://acme-corp.grafana.net or http://localhost:3000
          # Optional: Additional headers for all requests
          # additional_headers:
          #   X-Custom-Header: "custom-value"
    ```

    --8<-- "snippets/toolset_refresh_warning.md"

    To test, run:

    ```bash
    mavrick ask "Show me all dashboards tagged with 'kubernetes'"
    ```

=== "Mavrick Helm Chart"

    First, create a Kubernetes secret with your Grafana service account token:

    ```bash
    kubectl create secret generic grafana-api-key \
      --from-literal=api-key=your-grafana-service-account-token \
      -n mavrick
    ```

    --8<-- "snippets/secret_namespace_note.md"

    Then add to your Mavrick Helm values:

    ```yaml
    additionalEnvVars:
      - name: GRAFANA_API_KEY
        valueFrom:
          secretKeyRef:
            name: grafana-api-key
            key: api-key

    toolsets:
      grafana/dashboards:
        enabled: true
        config:
          api_key: "{{ env.GRAFANA_API_KEY }}"
          api_url: <your grafana url>  # e.g. https://acme-corp.grafana.net
          # Optional: Additional headers for all requests
          # additional_headers:
          #   X-Custom-Header: "custom-value"
    ```

=== "Robusta Helm Chart"

    First, create a Kubernetes secret with your Grafana service account token:

    ```bash
    kubectl create secret generic grafana-api-key \
      --from-literal=api-key=your-grafana-service-account-token \
      -n default
    ```

    --8<-- "snippets/secret_namespace_note.md"

    Then add to your Robusta Helm values:

    ```yaml
    mavrick:
      additionalEnvVars:
        - name: GRAFANA_API_KEY
          valueFrom:
            secretKeyRef:
              name: grafana-api-key
              key: api-key
      toolsets:
        grafana/dashboards:
          enabled: true
          config:
            api_key: "{{ env.GRAFANA_API_KEY }}"
            api_url: <your grafana url>  # e.g. https://acme-corp.grafana.net
            # Optional: Additional headers for all requests
            # additional_headers:
            #   X-Custom-Header: "custom-value"
    ```

    Apply the configuration:

    ```bash
    helm upgrade robusta robusta/robusta -f generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>
    ```

## Multiple Instances

```multi-instance
toolset: grafana/dashboards
name: Grafana
config: |
  api_url: <your grafana url>
  api_key: <your grafana service account token>
```

## Visual Rendering

When the Grafana Image Renderer is available, MavrickGPT can take screenshots of dashboards and panels and analyze them using the LLM's vision capabilities. This is useful for:

- Spotting anomalous spikes or patterns across many panels at once
- Analyzing visual dashboard layouts without parsing raw query data
- Investigating dashboards that use complex visualizations (heatmaps, gauges, etc.)

The LLM controls all rendering parameters — time range, dimensions, theme, timezone, and template variables — so it can zoom in on specific time windows or adjust the view as needed during investigation.

Rendering is **disabled by default**. To enable it, add `enable_rendering: true` to your config:

=== "Mavrick CLI"

    ```yaml
    toolsets:
      grafana/dashboards:
        enabled: true
        config:
          api_url: <your grafana url>
          api_key: <your api key>
          enable_rendering: true
    ```

=== "Mavrick Helm Chart"

    Reuses the `grafana-api-key` Kubernetes secret created in the [Configuration](#configuration) section above.

    ```yaml
    toolsets:
      grafana/dashboards:
        enabled: true
        config:
          api_url: <your grafana url>
          api_key: "{{ env.GRAFANA_API_KEY }}"
          enable_rendering: true
    ```

=== "Robusta Helm Chart"

    Reuses the `grafana-api-key` Kubernetes secret created in the [Configuration](#configuration) section above.

    ```yaml
    mavrick:
      toolsets:
        grafana/dashboards:
          enabled: true
          config:
            api_url: <your grafana url>
            api_key: "{{ env.GRAFANA_API_KEY }}"
            enable_rendering: true
    ```

When rendering a full dashboard, MavrickGPT captures the entire page (all rows) so that panels at the bottom are not cropped.

## Advanced Configuration

### SSL Verification

For self-signed certificates, you can disable SSL verification:

=== "Mavrick CLI"

    ```yaml
    toolsets:
      grafana/dashboards:
        enabled: true
        config:
          api_url: https://grafana.internal
          api_key: <your api key>
          verify_ssl: false  # Disable SSL verification (default: true)
    ```

=== "Mavrick Helm Chart"

    Reuses the `grafana-api-key` Kubernetes secret created in the [Configuration](#configuration) section above.

    ```yaml
    toolsets:
      grafana/dashboards:
        enabled: true
        config:
          api_url: https://grafana.internal
          api_key: "{{ env.GRAFANA_API_KEY }}"
          verify_ssl: false
    ```

=== "Robusta Helm Chart"

    Reuses the `grafana-api-key` Kubernetes secret created in the [Configuration](#configuration) section above.

    ```yaml
    mavrick:
      toolsets:
        grafana/dashboards:
          enabled: true
          config:
            api_url: https://grafana.internal
            api_key: "{{ env.GRAFANA_API_KEY }}"
            verify_ssl: false
    ```

### External URL

If MavrickGPT accesses Grafana through an internal URL but you want clickable links in results to use a different URL:

=== "Mavrick CLI"

    ```yaml
    toolsets:
      grafana/dashboards:
        enabled: true
        config:
          api_url: http://grafana.internal:3000  # Internal URL for API calls
          external_url: https://grafana.example.com  # URL for links in results
          api_key: <your api key>
    ```

=== "Mavrick Helm Chart"

    Reuses the `grafana-api-key` Kubernetes secret created in the [Configuration](#configuration) section above.

    ```yaml
    toolsets:
      grafana/dashboards:
        enabled: true
        config:
          api_url: http://grafana.internal:3000
          external_url: https://grafana.example.com
          api_key: "{{ env.GRAFANA_API_KEY }}"
    ```

=== "Robusta Helm Chart"

    Reuses the `grafana-api-key` Kubernetes secret created in the [Configuration](#configuration) section above.

    ```yaml
    mavrick:
      toolsets:
        grafana/dashboards:
          enabled: true
          config:
            api_url: http://grafana.internal:3000
            external_url: https://grafana.example.com
            api_key: "{{ env.GRAFANA_API_KEY }}"
    ```

## Common Use Cases

```bash
mavrick ask "Find all dashboards tagged with 'production' or 'kubernetes'"
```

```bash
mavrick ask "Show me what metrics the 'Node Exporter' dashboard monitors"
```

```bash
mavrick ask "Get the CPU usage queries from the Kubernetes cluster dashboard and check if any nodes are throttling"
```

```bash
mavrick ask "Look at the Platform Services dashboard and tell me if any panels show anomalous spikes"
```

```bash
mavrick ask "Render the checkout latency panel from the last 24 hours and analyze the trend"
```
