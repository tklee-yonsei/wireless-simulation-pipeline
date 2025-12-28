#!/bin/bash
set -e

echo "====================================="
echo "Cleaning Up Wireless Simulation Pipeline"
echo "====================================="

echo ""
echo "⚠️  This will delete all deployed resources"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled"
    exit 0
fi

echo ""
echo "🗑️  Deleting Control Pool..."
kubectl delete -f control-pool/deployment.yaml --ignore-not-found=true

echo ""
echo "🗑️  Deleting Monitor Pool..."
kubectl delete -f monitor-pool/deployment.yaml --ignore-not-found=true

echo ""
echo "🗑️  Deleting Calc Pool..."
kubectl delete -f calc-pool/deployment.yaml --ignore-not-found=true

echo ""
echo "🗑️  Deleting Scenario Pool..."
kubectl delete -f scenario-pool/deployment.yaml --ignore-not-found=true

echo ""
echo "🗑️  Deleting Storage Pool..."
kubectl delete -f storage-pool/deployment.yaml --ignore-not-found=true

echo ""
echo "🗑️  Deleting Queue System..."
kubectl delete -f queue-system/redis.yaml --ignore-not-found=true

echo ""
echo "⏳ Waiting for pods to terminate..."
sleep 10

echo ""
echo "🗑️  Deleting Namespaces..."
kubectl delete -f namespaces/create-namespaces.yaml --ignore-not-found=true

echo ""
echo "⏳ Waiting for namespaces to be removed..."
sleep 5

echo ""
echo "📊 Remaining resources:"
kubectl get all -A | grep -E "(control-pool|scenario-pool|calc-pool|monitor-pool|storage-pool|queue-system)" || echo "✅ All resources cleaned up"

echo ""
echo "====================================="
echo "✅ Cleanup Complete!"
echo "====================================="
echo ""
echo "ℹ️  K3s is still installed"
echo "To remove K3s completely, run:"
echo "   ./scripts/uninstall-k3s.sh"
echo ""
