#!/bin/bash
set -e

echo "====================================="
echo "Testing Wireless Simulation Pipeline"
echo "====================================="

# API Gateway URL
API_PORT=$(kubectl get svc api-gateway -n control-pool -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "30080")
API_URL="http://localhost:$API_PORT/api"

# WebSocket URL
WS_PORT=$(kubectl get svc monitor-service -n monitor-pool -o jsonpath='{.spec.ports[1].nodePort}' 2>/dev/null || echo "30082")
WS_URL="ws://localhost:$WS_PORT"

echo ""
echo "🔗 API Gateway: $API_URL"
echo "🔗 WebSocket: $WS_URL"
echo ""

# Health checks
echo "====================================="
echo "1️⃣  Health Checks"
echo "====================================="

echo ""
echo "Checking API Gateway..."
curl -s $API_URL/../health | python3 -m json.tool || echo "❌ API Gateway not responding"

echo ""
echo "Checking Monitor Service..."
MONITOR_HTTP_PORT=$(kubectl get svc monitor-service -n monitor-pool -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "30081")
curl -s http://localhost:$MONITOR_HTTP_PORT/health | python3 -m json.tool || echo "❌ Monitor Service not responding"

# Create Scenario
echo ""
echo "====================================="
echo "2️⃣  Creating Test Scenario"
echo "====================================="

SCENARIO_RESPONSE=$(curl -s -X POST $API_URL/scenario/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Scenario",
    "num_users": 10,
    "area_size": [1000, 1000],
    "duration": 60,
    "type": "urban_mobility"
  }')

echo "$SCENARIO_RESPONSE" | python3 -m json.tool

SCENARIO_ID=$(echo "$SCENARIO_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['scenario_id'])" 2>/dev/null || echo "")

if [ -z "$SCENARIO_ID" ]; then
    echo "❌ Failed to create scenario"
    exit 1
fi

echo ""
echo "✅ Scenario created: $SCENARIO_ID"

sleep 2

# Start Simulation
echo ""
echo "====================================="
echo "3️⃣  Starting Simulation"
echo "====================================="

SIMULATION_RESPONSE=$(curl -s -X POST $API_URL/simulation/start \
  -H "Content-Type: application/json" \
  -d "{\"scenario_id\": \"$SCENARIO_ID\"}")

echo "$SIMULATION_RESPONSE" | python3 -m json.tool

SIMULATION_ID=$(echo "$SIMULATION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['simulation_id'])" 2>/dev/null || echo "")

if [ -z "$SIMULATION_ID" ]; then
    echo "❌ Failed to start simulation"
    exit 1
fi

echo ""
echo "✅ Simulation started: $SIMULATION_ID"

sleep 3

# Check Queue Stats
echo ""
echo "====================================="
echo "4️⃣  Queue Statistics"
echo "====================================="

curl -s $API_URL/queue/stats | python3 -m json.tool

sleep 2

# Check Simulation Status
echo ""
echo "====================================="
echo "5️⃣  Simulation Status"
echo "====================================="

for i in {1..5}; do
    echo ""
    echo "Attempt $i/5..."
    STATUS_RESPONSE=$(curl -s $API_URL/simulation/status/$SIMULATION_ID)
    echo "$STATUS_RESPONSE" | python3 -m json.tool
    sleep 2
done

# Monitor Stats
echo ""
echo "====================================="
echo "6️⃣  Monitor Service Statistics"
echo "====================================="

curl -s http://localhost:$MONITOR_HTTP_PORT/stats | python3 -m json.tool

# List Results
echo ""
echo "====================================="
echo "7️⃣  Results List"
echo "====================================="

curl -s $API_URL/results/list | python3 -m json.tool

# Kubernetes Status
echo ""
echo "====================================="
echo "8️⃣  Kubernetes Pod Status"
echo "====================================="

echo ""
echo "All Pods:"
kubectl get pods -A | grep -E "(control-pool|scenario-pool|calc-pool|monitor-pool|storage-pool|queue-system)"

echo ""
echo "Worker Logs (last 10 lines):"
echo ""
echo "=== System Core ==="
kubectl logs -n calc-pool -l app=system-core --tail=10 2>/dev/null || echo "No logs available"

echo ""
echo "=== Channel Generator ==="
kubectl logs -n calc-pool -l app=channel-generator --tail=10 2>/dev/null || echo "No logs available"

echo ""
echo "=== PDP Interpolator ==="
kubectl logs -n calc-pool -l app=pdp-interpolator --tail=10 2>/dev/null || echo "No logs available"

# Summary
echo ""
echo "====================================="
echo "✅ Test Complete!"
echo "====================================="
echo ""
echo "📝 Summary:"
echo "   Scenario ID: $SCENARIO_ID"
echo "   Simulation ID: $SIMULATION_ID"
echo ""
echo "🌐 To monitor in real-time, open:"
echo "   file://$(pwd)/client/web-client.html"
echo ""
echo "💡 WebSocket URL for client:"
echo "   $WS_URL"
echo ""
