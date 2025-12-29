#!/bin/bash
set -e

echo "====================================="
echo "Deploying Monitoring Stack"
echo "====================================="

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

echo ""
echo "📦 Step 1: Creating monitoring namespace..."
kubectl apply -f monitoring/namespace.yaml
echo "✅ Monitoring namespace created"

sleep 2

echo ""
echo "📦 Step 2: Deploying kube-state-metrics..."
kubectl apply -f monitoring/kube-state-metrics.yaml
echo "✅ kube-state-metrics deployed"

sleep 2

echo ""
echo "📦 Step 3: Deploying node-exporter..."
kubectl apply -f monitoring/node-exporter.yaml
echo "✅ node-exporter deployed"

sleep 2

echo ""
echo "📦 Step 4: Deploying Prometheus..."
kubectl apply -f monitoring/prometheus.yaml
echo "✅ Prometheus deployed"

sleep 3

echo ""
echo "📦 Step 5: Deploying Grafana..."
kubectl apply -f monitoring/grafana.yaml
echo "✅ Grafana deployed"

sleep 3

echo ""
echo "📦 Step 6: Deploying Kubernetes Dashboard..."
kubectl apply -f monitoring/kubernetes-dashboard.yaml
echo "✅ Kubernetes Dashboard deployed"

echo ""
echo "⏳ Waiting for all monitoring pods to be ready..."
sleep 15

echo ""
echo "📊 Checking deployment status..."
echo ""
echo "=== Monitoring Namespace ==="
kubectl get pods -n monitoring
echo ""
echo "=== Kubernetes Dashboard ==="
kubectl get pods -n kubernetes-dashboard
echo ""

echo "📡 Monitoring Services:"
kubectl get svc -n monitoring
echo ""
kubectl get svc -n kubernetes-dashboard | grep kubernetes-dashboard
echo ""

# 대기 중인 Pod 확인
echo ""
echo "⏳ Waiting for Prometheus to be ready..."
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=120s 2>/dev/null || echo "   ⚠️  Prometheus is still starting..."

echo "⏳ Waiting for Grafana to be ready..."
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=120s 2>/dev/null || echo "   ⚠️  Grafana is still starting..."

echo "⏳ Waiting for Kubernetes Dashboard to be ready..."
kubectl wait --for=condition=ready pod -l app=kubernetes-dashboard -n kubernetes-dashboard --timeout=120s 2>/dev/null || echo "   ⚠️  Dashboard is still starting..."

echo ""
echo "====================================="
echo "✅ Monitoring Stack Deployment Complete!"
echo "====================================="
echo ""
echo "🔗 Access URLs:"
echo ""
echo "📊 Prometheus:"
echo "   http://localhost:30090"
echo ""
echo "📈 Grafana:"
echo "   http://localhost:30091"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🎛️  Kubernetes Dashboard:"
echo "   http://localhost:30092"
echo ""
echo "🔑 To get Dashboard admin token:"
echo "   kubectl get secret admin-user-token -n kubernetes-dashboard -o jsonpath='{.data.token}' | base64 -d && echo"
echo ""
echo "💡 Pre-configured Grafana Dashboards:"
echo "   - Wireless Simulation Pipeline"
echo "   - Kubernetes Cluster"
echo ""

