#!/bin/bash
set -e

echo "====================================="
echo "Deploying Wireless Simulation Pipeline"
echo "====================================="

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# --no-cache로 빌드된 풀 목록 (환경변수로 전달받음)
# deploy-to-remote.sh에서 NO_CACHE_POOLS 환경변수로 전달
NO_CACHE_POOLS="${NO_CACHE_POOLS:-}"

# 특정 풀이 no-cache 목록에 있는지 확인하는 함수
should_restart_deployment() {
    local pool_name=$1
    if [ -z "$NO_CACHE_POOLS" ]; then
        return 1  # false
    fi
    # 공백으로 구분된 목록에서 찾기
    for pool in $NO_CACHE_POOLS; do
        if [ "$pool" = "$pool_name" ]; then
            return 0  # true
        fi
    done
    return 1  # false
}

# 풀 이름을 네임스페이스와 Deployment 이름으로 매핑하는 함수
restart_deployment_if_needed() {
    local pool_name=$1
    local namespace=$2
    local deployment_name=$3
    
    if should_restart_deployment "$pool_name"; then
        echo "   🔄 Restarting $pool_name deployment (no-cache build detected)..."
        kubectl rollout restart deployment/$deployment_name -n $namespace
    fi
}

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
restart_deployment_if_needed "storage-pool" "storage-pool" "storage-service"
echo "✅ Storage Pool deployed"

sleep 3

echo ""
echo "📦 Step 4: Deploying Scenario Pool..."
kubectl apply -f scenario-pool/deployment.yaml
restart_deployment_if_needed "scenario-pool" "scenario-pool" "scenario-service"
echo "✅ Scenario Pool deployed"

sleep 3

echo ""
echo "📦 Step 5: Deploying Calc Pool..."
kubectl apply -f calc-pool/deployment.yaml
if should_restart_deployment "calc-pool"; then
    echo "   🔄 Restarting calc-pool deployments (no-cache build detected)..."
    kubectl rollout restart deployment/system-core -n calc-pool
    kubectl rollout restart deployment/channel-generator -n calc-pool
    kubectl rollout restart deployment/pdp-interpolator -n calc-pool
fi
echo "✅ Calc Pool deployed"

sleep 3

echo ""
echo "📦 Step 6: Deploying Monitor Pool..."
kubectl apply -f monitor-pool/deployment.yaml
restart_deployment_if_needed "monitor-pool" "monitor-pool" "monitor-service"
echo "✅ Monitor Pool deployed"

sleep 5

echo ""
echo "📦 Step 7: Deploying Control Pool (API Gateway)..."
kubectl apply -f control-pool/deployment.yaml
restart_deployment_if_needed "control-pool" "control-pool" "api-gateway"
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
