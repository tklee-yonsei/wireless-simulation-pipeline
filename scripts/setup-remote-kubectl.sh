#!/bin/bash
set -e

# ===================================
# 원격 K3s 클러스터 kubectl 설정
# Mac/로컬에서 원격 서버 제어용
# ===================================

REMOTE_USER="${REMOTE_USER:-ubuntu}"
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_PORT="${REMOTE_PORT:-22}"
CONTEXT_NAME="${CONTEXT_NAME:-remote-k3s}"
USE_TUNNEL="${USE_TUNNEL:-false}"

# 사용법 출력
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -u, --user USER       Remote user (default: ubuntu)"
    echo "  -h, --host HOST       Remote host (required)"
    echo "  -P, --port PORT       SSH port (default: 22)"
    echo "  -c, --context NAME    Context name (default: remote-k3s)"
    echo "  --tunnel              Use SSH tunnel for API access (port 6443)"
    echo "  --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -h 192.168.1.100"
    echo "  $0 -u ubuntu -h my-server.com -P 2222 -c production"
    echo "  $0 -h my-server.com --tunnel  # Use SSH tunnel (no need to open port 6443)"
    echo "  REMOTE_HOST=my-server.com REMOTE_PORT=2222 $0"
    exit 1
}

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--user)
            REMOTE_USER="$2"
            shift 2
            ;;
        -h|--host)
            REMOTE_HOST="$2"
            shift 2
            ;;
        -P|--port)
            REMOTE_PORT="$2"
            shift 2
            ;;
        -c|--context)
            CONTEXT_NAME="$2"
            shift 2
            ;;
        --tunnel)
            USE_TUNNEL=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# 필수 파라미터 확인
if [ -z "$REMOTE_HOST" ]; then
    echo "❌ Error: Remote host is required"
    echo ""
    usage
fi

echo "====================================="
echo "Setup Remote kubectl Access"
echo "====================================="
echo "Remote Host: ${REMOTE_USER}@${REMOTE_HOST}"
echo "SSH Port: ${REMOTE_PORT}"
echo "Context Name: ${CONTEXT_NAME}"
if [ "$USE_TUNNEL" = true ]; then
    echo "Mode: SSH Tunnel (port 6443 not required)"
else
    echo "Mode: Direct Access (port 6443 must be open)"
fi
echo "====================================="
echo ""

# kubectl 확인
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    echo ""
    echo "Install kubectl:"
    echo "  macOS: brew install kubectl"
    echo "  Linux: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# 연결 테스트
echo "🔍 Testing connection..."
if ! ssh -p ${REMOTE_PORT} -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} "echo 'OK'" > /dev/null 2>&1; then
    echo "❌ Failed to connect to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}"
    exit 1
fi
echo "✅ Connection successful"
echo ""

# kubeconfig 디렉토리 생성 (홈 디렉토리 사용)
KUBE_DIR="${HOME}/.kube"
mkdir -p "${KUBE_DIR}"

# 원격 kubeconfig 다운로드
echo "📥 Downloading kubeconfig from remote server..."
ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "sudo cat /etc/rancher/k3s/k3s.yaml" > /tmp/k3s-remote.yaml

if [ ! -s /tmp/k3s-remote.yaml ]; then
    echo "❌ Failed to download kubeconfig"
    echo "Make sure K3s is installed on the remote server"
    exit 1
fi

# 서버 주소 수정
echo "🔧 Configuring kubeconfig..."
if [ "$USE_TUNNEL" = true ]; then
    # SSH 터널링 사용 시 localhost 사용
    sed "s/127.0.0.1/localhost/g" /tmp/k3s-remote.yaml > "${KUBE_DIR}/config-${CONTEXT_NAME}"
    echo "ℹ️  Using SSH tunnel mode - you need to keep SSH tunnel running:"
    echo "   ssh -p ${REMOTE_PORT} -L 6443:localhost:6443 ${REMOTE_USER}@${REMOTE_HOST}"
    echo ""
    echo "⚠️  IMPORTANT: Start the SSH tunnel in a separate terminal before using kubectl!"
else
    # 직접 접속 시 실제 서버 IP 사용
    sed "s/127.0.0.1/${REMOTE_HOST}/g" /tmp/k3s-remote.yaml > "${KUBE_DIR}/config-${CONTEXT_NAME}"
    echo "ℹ️  Using direct access mode - port 6443 must be open on server"
fi

# Context 이름 확인 및 변경
CURRENT_CONTEXT=$(kubectl config --kubeconfig="${KUBE_DIR}/config-${CONTEXT_NAME}" view -o jsonpath='{.contexts[0].name}' 2>/dev/null || echo "")
if [ -z "$CURRENT_CONTEXT" ] || [ "$CURRENT_CONTEXT" != "${CONTEXT_NAME}" ]; then
    # Context 이름이 없거나 다르면 변경 시도
    if [ "$CURRENT_CONTEXT" = "default" ]; then
        kubectl config --kubeconfig="${KUBE_DIR}/config-${CONTEXT_NAME}" rename-context default ${CONTEXT_NAME} 2>/dev/null || true
    else
        # Context가 없으면 새로 생성
        kubectl config --kubeconfig="${KUBE_DIR}/config-${CONTEXT_NAME}" set-context ${CONTEXT_NAME} --cluster=default --user=default 2>/dev/null || true
    fi
fi

# 기존 config와 병합
if [ -f "${KUBE_DIR}/config" ]; then
    echo "🔗 Merging with existing kubeconfig..."
    cp "${KUBE_DIR}/config" "${KUBE_DIR}/config.backup"
    
    # 기존 context가 있으면 제거 (중복 방지)
    kubectl config delete-context ${CONTEXT_NAME} 2>/dev/null || true
    
    # 병합
    KUBECONFIG="${KUBE_DIR}/config:${KUBE_DIR}/config-${CONTEXT_NAME}" kubectl config view --flatten > "${KUBE_DIR}/config.tmp"
    mv "${KUBE_DIR}/config.tmp" "${KUBE_DIR}/config"
else
    cp "${KUBE_DIR}/config-${CONTEXT_NAME}" "${KUBE_DIR}/config"
fi

# 권한 설정
chmod 600 "${KUBE_DIR}/config"

# Context가 제대로 설정되었는지 확인
if kubectl config get-contexts ${CONTEXT_NAME} > /dev/null 2>&1; then
    echo "✅ Context '${CONTEXT_NAME}' configured"
else
    echo "⚠️  Warning: Context may not be properly configured"
    echo "   Available contexts:"
    kubectl config get-contexts || true
fi

# 임시 파일 삭제
rm -f /tmp/k3s-remote.yaml "${KUBE_DIR}/config-${CONTEXT_NAME}"

echo "✅ kubeconfig configured successfully"
echo ""

# Context 전환
if kubectl config use-context ${CONTEXT_NAME} 2>/dev/null; then
    echo "✅ Switched to context: ${CONTEXT_NAME}"
else
    echo "⚠️  Warning: Could not switch to context ${CONTEXT_NAME}"
    echo "   Available contexts:"
    kubectl config get-contexts || true
    echo ""
    echo "   You can manually switch with: kubectl config use-context ${CONTEXT_NAME}"
fi

echo ""
echo "====================================="
echo "✅ Setup Complete!"
echo "====================================="
echo ""
echo "Current context: $(kubectl config current-context 2>/dev/null || echo 'none')"
echo ""

# 연결 테스트
echo "🧪 Testing cluster connection..."
if [ "$USE_TUNNEL" = true ]; then
    echo "⚠️  Note: Make sure SSH tunnel is running:"
    echo "   ssh -p ${REMOTE_PORT} -L 6443:localhost:6443 ${REMOTE_USER}@${REMOTE_HOST}"
    echo ""
fi

if kubectl cluster-info > /dev/null 2>&1; then
    echo "✅ Successfully connected to remote cluster"
    echo ""
    kubectl get nodes
    echo ""
else
    echo "❌ Failed to connect to cluster"
    if [ "$USE_TUNNEL" = true ]; then
        echo ""
        echo "Possible issues:"
        echo "  1. SSH tunnel is not running - start it with:"
        echo "     ssh -p ${REMOTE_PORT} -L 6443:localhost:6443 ${REMOTE_USER}@${REMOTE_HOST}"
        echo "  2. K3s is not running on the remote server"
    else
        echo ""
        echo "Possible issues:"
        echo "  1. Port 6443 is not open on the server"
        echo "  2. K3s is not running on the remote server"
        echo "  3. Firewall is blocking the connection"
    fi
    exit 1
fi

echo "💡 Useful commands:"
echo "  kubectl get pods -A                    # View all pods"
echo "  kubectl get nodes                      # View nodes"
echo "  kubectl logs -n control-pool -l app=api-gateway -f"
echo ""
echo "💡 Switch context:"
echo "  kubectl config get-contexts            # List contexts"
echo "  kubectl config use-context ${CONTEXT_NAME}"
echo ""
if [ "$USE_TUNNEL" = true ]; then
    echo "⚠️  IMPORTANT: Keep SSH tunnel running in a separate terminal:"
    echo "   ssh -p ${REMOTE_PORT} -L 6443:localhost:6443 ${REMOTE_USER}@${REMOTE_HOST}"
    echo ""
fi
echo "💡 Backup created at: ${KUBE_DIR}/config.backup"
echo ""

