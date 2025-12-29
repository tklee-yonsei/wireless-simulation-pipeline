#!/bin/bash
set -e

echo "====================================="
echo "Cleaning up Monitoring Stack"
echo "====================================="

cd "$(dirname "$0")/.."

echo ""
echo "🗑️  Removing Kubernetes Dashboard..."
kubectl delete -f monitoring/kubernetes-dashboard.yaml --ignore-not-found=true
echo "✅ Kubernetes Dashboard removed"

echo ""
echo "🗑️  Removing Grafana..."
kubectl delete -f monitoring/grafana.yaml --ignore-not-found=true
echo "✅ Grafana removed"

echo ""
echo "🗑️  Removing Prometheus..."
kubectl delete -f monitoring/prometheus.yaml --ignore-not-found=true
echo "✅ Prometheus removed"

echo ""
echo "🗑️  Removing node-exporter..."
kubectl delete -f monitoring/node-exporter.yaml --ignore-not-found=true
echo "✅ node-exporter removed"

echo ""
echo "🗑️  Removing kube-state-metrics..."
kubectl delete -f monitoring/kube-state-metrics.yaml --ignore-not-found=true
echo "✅ kube-state-metrics removed"

echo ""
echo "🗑️  Removing monitoring namespace..."
kubectl delete -f monitoring/namespace.yaml --ignore-not-found=true
echo "✅ Monitoring namespace removed"

echo ""
echo "🗑️  Removing kubernetes-dashboard namespace..."
kubectl delete namespace kubernetes-dashboard --ignore-not-found=true
echo "✅ Kubernetes Dashboard namespace removed"

echo ""
echo "====================================="
echo "✅ Monitoring Stack Cleanup Complete!"
echo "====================================="

