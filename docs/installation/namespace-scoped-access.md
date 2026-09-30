# Limiting Mavrick to a Namespace

By default, the Mavrick Helm chart creates a cluster-wide, read-only `ClusterRole` so Mavrick can investigate resources across the whole cluster. This guide explains how to instead restrict Mavrick to a single namespace.

## What to Expect

When Mavrick is scoped to one namespace, it can only see resources in that namespace. Tools that query cluster-scoped resources (nodes, persistent volumes, storage classes, CRDs) or that list across all namespaces (`kubectl get ... --all-namespaces`, `kubectl top pods -A`) will return `forbidden` errors. Mavrick keeps running and simply reports those errors, but investigations are limited to the target namespace.

## Scope Mavrick to Its Own Namespace

To limit Mavrick to the namespace it is deployed in, set one Helm value:

```yaml
namespaceScopedRBAC: true
```

The chart then renders a namespaced `Role` + `RoleBinding` (same read rules) instead of the `ClusterRole` + `ClusterRoleBinding`, and sets the `SCOPED_NAMESPACES` environment variable so Mavrick knows its scope up front — investigations start with namespace-scoped commands instead of discovering the restriction from `forbidden` errors. Everything stays Helm-managed, and multiple Mavrick installs in different namespaces cannot collide on cluster-scoped RBAC names.

To scope Mavrick to a **different** set of namespaces than its own, use the manual configuration below.

## Manual Configuration

Point Mavrick at your own service account instead of the chart-managed cluster-wide one.

Set the following in your Helm values:

```yaml
# Don't let the chart create its cluster-wide ClusterRole/ClusterRoleBinding
createServiceAccount: false
# Use the namespace-scoped service account you create below
customServiceAccountName: mavrick
# Tell Mavrick its scope so investigations start namespace-scoped
# instead of discovering the restriction from forbidden errors
additionalEnvVars:
  - name: SCOPED_NAMESPACES
    value: "monitoring"   # comma-separated for multiple namespaces
```

Create the service account, `Role`, and `RoleBinding` (`mavrick-namespace-scoped.yaml`).

!!! warning "The service account must live in the namespace where Mavrick is deployed"
    Create the `ServiceAccount` in the **same namespace where the Mavrick agent runs** (the release namespace, e.g. the namespace you pass to `helm install ... -n <namespace>`). If it is created in a different namespace, Mavrick' pod won't be able to use it and the setup will not work. The `RoleBinding` in the target namespace then references this service account by its name **and** its namespace.

In the manifest below, replace:

- `monitoring` — the namespace you want Mavrick to investigate
- `<MAVRICK_NAMESPACE>` — the namespace where the Mavrick agent is deployed (both places it appears)

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mavrick
  # Must match the namespace where the Mavrick agent is deployed
  namespace: <MAVRICK_NAMESPACE>

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: mavrick-namespace-scoped
  namespace: monitoring
rules:
  - apiGroups: [""]
    resources:
      - configmaps
      - endpoints
      - events
      - persistentvolumeclaims
      - pods
      - pods/log
      - pods/status
      - replicationcontrollers
      - services
      - serviceaccounts
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources:
      - daemonsets
      - deployments
      - replicasets
      - statefulsets
    verbs: ["get", "list", "watch"]
  - apiGroups: ["batch"]
    resources:
      - cronjobs
      - jobs
    verbs: ["get", "list", "watch"]
  - apiGroups: ["autoscaling"]
    resources:
      - horizontalpodautoscalers
    verbs: ["get", "list", "watch"]
  - apiGroups: ["networking.k8s.io"]
    resources:
      - ingresses
      - networkpolicies
    verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: mavrick-namespace-scoped
  namespace: monitoring
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: mavrick-namespace-scoped
subjects:
  - kind: ServiceAccount
    name: mavrick
    # Must match the namespace where the Mavrick agent is deployed
    namespace: <MAVRICK_NAMESPACE>
```

Apply it, then upgrade Mavrick with the values above:

```bash
kubectl apply -f mavrick-namespace-scoped.yaml
```

To grant access to more than one namespace, create an additional `Role` + `RoleBinding` in each namespace, all bound to the same `mavrick` service account (still referencing it in its own `<MAVRICK_NAMESPACE>`).

## Verify the Configuration

```bash
# Confirm the Role and binding exist in the target namespace
kubectl get role mavrick-namespace-scoped -n monitoring
kubectl get rolebinding mavrick-namespace-scoped -n monitoring

# Check what the service account can and cannot do
# Replace <MAVRICK_NAMESPACE> with the namespace where Mavrick is deployed before running these commands.
# Format: system:serviceaccount:<MAVRICK_NAMESPACE>:<serviceaccount-name>
kubectl auth can-i list pods -n monitoring --as=system:serviceaccount:<MAVRICK_NAMESPACE>:mavrick
kubectl auth can-i list nodes --as=system:serviceaccount:<MAVRICK_NAMESPACE>:mavrick  # expected: no
```
