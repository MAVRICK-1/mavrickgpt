# Crossplane

By enabling this toolset, MavrickGPT will be able to troubleshoot Crossplane-managed infrastructure by inspecting providers, compositions, claims, composite resources, and managed resources across the full resource hierarchy.

## Prerequisites

Crossplane must be installed on your Kubernetes cluster. MavrickGPT uses `kubectl` to query Crossplane custom resources, so no additional CLI tools are required.

MavrickGPT needs read access to Crossplane CRDs. If you use Kubernetes RBAC, ensure the service account has permissions to `get` and `list` the following API groups:

```yaml
# Add to your ClusterRole
- apiGroups: ["pkg.crossplane.io"]
  resources: ["providers", "providerrevisions"]
  verbs: ["get", "list"]
- apiGroups: ["apiextensions.crossplane.io"]
  resources: ["compositeresourcedefinitions", "compositions"]
  verbs: ["get", "list"]
# For managed resources, add the specific API groups used by your providers.
# Example for AWS provider:
- apiGroups: ["s3.aws.upbound.io", "rds.aws.upbound.io", "ec2.aws.upbound.io"]
  resources: ["*"]
  verbs: ["get", "list"]
```

## Configuration

=== "Mavrick CLI"

    Add the following to **~/.mavrick/config.yaml**:

    ```yaml
    toolsets:
        crossplane/core:
            enabled: true
    ```

    --8<-- "snippets/toolset_refresh_warning.md"

    To test, run:

    ```bash
    mavrick ask "Which Crossplane managed resources are failing and why?"
    ```

=== "Robusta Helm Chart"

    ```yaml
    mavrick:
        customClusterRoleRules:
            - apiGroups: ["pkg.crossplane.io"]
              resources: ["providers", "providerrevisions"]
              verbs: ["get", "list"]
            - apiGroups: ["apiextensions.crossplane.io"]
              resources: ["compositeresourcedefinitions", "compositions"]
              verbs: ["get", "list"]
        toolsets:
            crossplane/core:
                enabled: true
    ```

    Apply the configuration:

    ```bash
    helm upgrade robusta robusta/robusta -f generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>
    ```

## Common Use Cases

```bash
mavrick ask "Which Crossplane managed resources are failing and why?"
```

```bash
mavrick ask "Are all Crossplane providers healthy?"
```

```bash
mavrick ask "Trace the claim my-database in namespace production and find which managed resource is broken"
```

```bash
mavrick ask "Why is my S3 bucket not becoming ready?"
```
