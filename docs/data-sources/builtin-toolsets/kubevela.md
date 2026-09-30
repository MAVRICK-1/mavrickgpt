# KubeVela

This toolset provides access to KubeVela CLI commands for managing and troubleshooting applications built on the Open Application Model (OAM).

## Prerequisites

The KubeVela CLI (`vela`) must be installed and configured to access your cluster.

**Installation:**

```bash
# Install vela CLI
curl -fsSl https://kubevela.io/script/install.sh | bash

# Verify installation
vela version
```

## Configuration

=== "Mavrick CLI"

    Add the following to **~/.mavrick/config.yaml**:

    <!-- markdownlint-disable-next-line MD046 -->
    ```yaml
    toolsets:
        kubevela/core:
            enabled: true
    ```

    --8<-- "snippets/toolset_refresh_warning.md"

    To test, run:

    ```bash
    mavrick ask "What is the status of my KubeVela applications?"
    ```

## Common Use Cases

```bash
mavrick ask "What KubeVela applications are unhealthy and why?"
```

```bash
mavrick ask "Show me the workflow status for my payment-service application"
```

```bash
mavrick ask "What components does my frontend application have and are they running correctly?"
```

```bash
mavrick ask "Check if there are any trait configuration issues in the user-api application"
```
