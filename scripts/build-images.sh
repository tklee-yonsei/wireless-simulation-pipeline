#!/bin/bash
set -e

echo "====================================="
echo "Building Docker Images"
echo "====================================="

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

echo ""
echo "🔨 Building Storage Pool image..."
docker build -t storage-pool:latest ./storage-pool
docker save storage-pool:latest -o /tmp/storage-pool.tar
# sudo 없이 시도하고, 실패하면 sudo 사용
if k3s ctr images import /tmp/storage-pool.tar 2>/dev/null; then
    echo "✅ Imported without sudo"
else
    echo "⚠️  Trying with sudo (password may be required)..."
    sudo k3s ctr images import /tmp/storage-pool.tar
fi
rm /tmp/storage-pool.tar
echo "✅ Storage Pool image ready"

echo ""
echo "🔨 Building Scenario Pool image..."
docker build -t scenario-pool:latest ./scenario-pool
docker save scenario-pool:latest -o /tmp/scenario-pool.tar
if k3s ctr images import /tmp/scenario-pool.tar 2>/dev/null; then
    echo "✅ Imported without sudo"
else
    sudo k3s ctr images import /tmp/scenario-pool.tar
fi
rm /tmp/scenario-pool.tar
echo "✅ Scenario Pool image ready"

echo ""
echo "🔨 Building Calc Pool image..."
docker build -t calc-pool:latest ./calc-pool
docker save calc-pool:latest -o /tmp/calc-pool.tar
if k3s ctr images import /tmp/calc-pool.tar 2>/dev/null; then
    echo "✅ Imported without sudo"
else
    sudo k3s ctr images import /tmp/calc-pool.tar
fi
rm /tmp/calc-pool.tar
echo "✅ Calc Pool image ready"

echo ""
echo "🔨 Building Monitor Pool image..."
docker build -t monitor-pool:latest ./monitor-pool
docker save monitor-pool:latest -o /tmp/monitor-pool.tar
if k3s ctr images import /tmp/monitor-pool.tar 2>/dev/null; then
    echo "✅ Imported without sudo"
else
    sudo k3s ctr images import /tmp/monitor-pool.tar
fi
rm /tmp/monitor-pool.tar
echo "✅ Monitor Pool image ready"

echo ""
echo "🔨 Building Control Pool image..."
docker build -t control-pool:latest ./control-pool
docker save control-pool:latest -o /tmp/control-pool.tar
if k3s ctr images import /tmp/control-pool.tar 2>/dev/null; then
    echo "✅ Imported without sudo"
else
    sudo k3s ctr images import /tmp/control-pool.tar
fi
rm /tmp/control-pool.tar
echo "✅ Control Pool image ready"

echo ""
echo "====================================="
echo "✅ All Images Built Successfully!"
echo "====================================="
echo ""
echo "Verifying images in K3s..."
if k3s ctr images list 2>/dev/null | grep -E "(storage-pool|scenario-pool|calc-pool|monitor-pool|control-pool)"; then
    echo "✅ Images verified"
else
    sudo k3s ctr images list | grep -E "(storage-pool|scenario-pool|calc-pool|monitor-pool|control-pool)"
fi
echo ""
