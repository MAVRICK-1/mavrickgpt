#!/bin/bash
set -e

# Clean up the restricted access resources
kubectl delete clusterrole test-clusterrole-28 --ignore-not-found
kubectl delete secret restricted-mavrick-sa-token -n 28-test --ignore-not-found
kubectl delete clusterrolebinding restricted-mavrick-binding-28 --ignore-not-found
kubectl delete clusterrole restricted-mavrick-role-28 --ignore-not-found
kubectl delete serviceaccount restricted-mavrick-sa -n 28-test --ignore-not-found

# Delete the test namespace
kubectl delete namespace 28-test --ignore-not-found

# Clean up temporary directory and kubeconfig (fixed path, see setup script)
rm -rf "/tmp/mavrick-test-28-permissions" 2>/dev/null || true
