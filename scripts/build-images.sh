#!/bin/bash
set -e

echo "====================================="
echo "Building Docker Images"
echo "====================================="

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# --no-cache로 빌드할 풀 목록 (환경변수 또는 인자로 전달)
# 예: NO_CACHE_POOLS="control-pool calc-pool" 또는 --no-cache control-pool calc-pool
NO_CACHE_POOLS="${NO_CACHE_POOLS:-}"

# 특정 풀이 no-cache 목록에 있는지 확인하는 함수
should_use_no_cache() {
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

echo ""
echo "🔨 Building Storage Pool image..."
if should_use_no_cache "storage-pool"; then
    echo "   Using --no-cache option"
    docker build --no-cache -t storage-pool:latest ./storage-pool
else
    docker build -t storage-pool:latest ./storage-pool
fi
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
if should_use_no_cache "scenario-pool"; then
    echo "   Using --no-cache option"
    docker build --no-cache -t scenario-pool:latest ./scenario-pool
else
    docker build -t scenario-pool:latest ./scenario-pool
fi
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
if should_use_no_cache "calc-pool"; then
    echo "   Using --no-cache option"
    docker build --no-cache -t calc-pool:latest ./calc-pool
else
    docker build -t calc-pool:latest ./calc-pool
fi
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
if should_use_no_cache "monitor-pool"; then
    echo "   Using --no-cache option"
    docker build --no-cache -t monitor-pool:latest ./monitor-pool
else
    docker build -t monitor-pool:latest ./monitor-pool
fi
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
# control-pool은 client 폴더가 필요하므로 프로젝트 루트를 빌드 컨텍스트로 사용
if should_use_no_cache "control-pool"; then
    echo "   Using --no-cache option"
    docker build --no-cache -t control-pool:latest -f ./control-pool/Dockerfile .
else
    docker build -t control-pool:latest -f ./control-pool/Dockerfile .
fi
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
