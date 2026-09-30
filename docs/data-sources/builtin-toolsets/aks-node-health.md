# AKS Node Health

!!! tip "Consider Azure MCP instead"
    Most users should start with the [Azure MCP](azure-mcp.md) integration, which provides broad access to all Azure APIs including AKS node diagnostics. This standalone toolset is only needed if you require specific AKS node health CLI commands that aren't available through the MCP server.

By enabling this toolset, MavrickGPT will be able to perform specialized health checks and troubleshooting for Azure Kubernetes Service (AKS) nodes, including node-specific diagnostics and performance analysis.

## Prerequisites

1. Azure CLI installed and configured
2. Appropriate Azure RBAC permissions for AKS clusters
3. Access to the target AKS cluster
4. Node-level access permissions

## Configuration

=== "Mavrick CLI"

    First, ensure you're authenticated with Azure:

    ```bash
    az login
    az account set --subscription "<your subscription id>"
    ```

    Then add the following to **~/.mavrick/config.yaml**. Create the file if it doesn't exist:

    ```yaml
    toolsets:
      aks/node-health:
        enabled: true
        config:
          subscription_id: "<your Azure subscription ID>"
          resource_group: "<your AKS resource group>"
          cluster_name: "<your AKS cluster name>"
    ```

    --8<-- "snippets/toolset_refresh_warning.md"

=== "Mavrick Helm Chart"

    When using the **standalone Mavrick Helm Chart**, update your `values.yaml`:

    ```yaml
    toolsets:
      aks/node-health:
        enabled: true
        config:
          subscription_id: "<your Azure subscription ID>"
          resource_group: "<your AKS resource group>"
          cluster_name: "<your AKS cluster name>"
    ```

    Apply the configuration:

    ```bash
    helm upgrade mavrick robusta/mavrick -f values.yaml
    ```

=== "Robusta Helm Chart"

    When using the **Robusta Helm Chart** (which includes MavrickGPT), update your `generated_values.yaml`:

    ```yaml
    mavrick:
      toolsets:
        aks/node-health:
          enabled: true
          config:
            subscription_id: "<your Azure subscription ID>"
            resource_group: "<your AKS resource group>"
            cluster_name: "<your AKS cluster name>"
    ```

    Apply the configuration:

    ```bash
    helm upgrade robusta robusta/robusta -f generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>
    ```

## Advanced Configuration

You can configure additional health check parameters:

```yaml
toolsets:
  aks/node-health:
    enabled: true
    config:
      subscription_id: "<your Azure subscription ID>"
      resource_group: "<your AKS resource group>"
      cluster_name: "<your AKS cluster name>"
      health_check_interval: 300  # Health check interval in seconds
      max_unhealthy_nodes: 3  # Maximum number of unhealthy nodes to report
```

## Capabilities

| Tool Name | Description |
|-----------|-------------|
| aks_check_node_health | Perform comprehensive health checks on AKS nodes |
| aks_get_node_metrics | Get detailed metrics for AKS nodes |
| aks_diagnose_node_issues | Diagnose common node-level issues |
| aks_check_node_readiness | Check if nodes are ready and schedulable |
| aks_get_node_events | Get events related to specific nodes |
| aks_check_node_resources | Check resource utilization on nodes |
