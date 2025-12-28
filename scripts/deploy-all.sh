#!/bin/bash
set -e

echo "====================================="
echo "Deploying Wireless Simulation Pipeline"
echo "====================================="

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

echo ""
echo "📦 Step 1: Creating namespaces..."
kubectl apply -f namespaces/create-namespaces.yaml
echo "✅ Namespaces created"

sleep 2

echo ""
echo "📦 Step 2: Deploying Queue System (Redis)..."
kubectl apply -f queue-system/redis.yaml
echo "✅ Redis deployed"

sleep 5

echo ""
echo "📦 Step 3: Deploying Storage Pool..."
kubectl apply -f storage-pool/deployment.yaml
echo "✅ Storage Pool deployed"

sleep 3

echo ""
echo "📦 Step 4: Deploying Scenario Pool..."
kubectl apply -f scenario-pool/deployment.yaml
echo "✅ Scenario Pool deployed"

sleep 3

echo ""
echo "📦 Step 5: Deploying Calc Pool..."
kubectl apply -f calc-pool/deployment.yaml
echo "✅ Calc Pool deployed"

sleep 3

echo ""
echo "📦 Step 6: Deploying Monitor Pool..."
kubectl apply -f monitor-pool/deployment.yaml
echo "✅ Monitor Pool deployed"

sleep 5

echo ""
echo "📦 Step 7: Deploying Control Pool (API Gateway)..."
kubectl apply -f control-pool/deployment.yaml
echo "✅ Control Pool deployed"

echo ""
echo "⏳ Waiting for all pods to be ready..."
sleep 10

echo ""
echo "📊 Checking deployment status..."
echo ""
echo "=== Queue System ==="
kubectl get pods -n queue-system
echo ""
echo "=== Storage Pool ==="
kubectl get pods -n storage-pool
echo ""
echo "=== Scenario Pool ==="
kubectl get pods -n scenario-pool
echo ""
echo "=== Calc Pool ==="
kubectl get pods -n calc-pool
echo ""
echo "=== Monitor Pool ==="
kubectl get pods -n monitor-pool
echo ""
echo "=== Control Pool ==="
kubectl get pods -n control-pool
echo ""

echo "📡 Services:"
kubectl get svc -A | grep -E "(control-pool|monitor-pool)"

echo ""
echo "====================================="
echo "✅ Deployment Complete!"
echo "====================================="
echo ""
echo "🌐 API Gateway:"
API_PORT=$(kubectl get svc api-gateway -n control-pool -o jsonpath='{.spec.ports[0].nodePort}')
echo "   http://localhost:$API_PORT"
echo ""
echo "📊 Monitor Service:"
WS_PORT=$(kubectl get svc monitor-service -n monitor-pool -o jsonpath='{.spec.ports[1].nodePort}')
echo "   WebSocket: ws://localhost:$WS_PORT"
echo ""
echo "🌐 Open the web client:"
echo "   file://$(pwd)/client/web-client.html"
echo ""
echo "💡 Test the pipeline:"
echo "   ./scripts/test-pipeline.sh"
echo ""
