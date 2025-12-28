#!/bin/bash
set -e

# ===================================
# 원격 Ubuntu 서버 배포 스크립트
# ===================================
# 
# 사용 방법:
#   ./scripts/deploy-to-remote.sh -h <server-ip>
#
# GitHub Actions에서도 사용 가능:
#   - 환경변수로 REMOTE_HOST, REMOTE_USER 설정
#   - SSH 키는 GitHub Secrets에 저장
#   - 예: REMOTE_HOST=${{ secrets.REMOTE_HOST }} ./scripts/deploy-to-remote.sh
#

# 설정 (사용자 환경에 맞게 수정)
# 기본값: ubuntu 사용자, 하지만 -u 옵션으로 다른 사용자 지정 가능
REMOTE_USER="${REMOTE_USER:-ubuntu}"
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_PORT="${REMOTE_PORT:-22}"
# REMOTE_PATH는 인자 파싱 후에 설정됨
# -p 옵션으로 명시적으로 지정하지 않으면, REMOTE_USER의 홈 디렉토리 기반으로 자동 생성
# 예: -u myuser → /home/myuser/wireless-simulation-pipeline
REMOTE_PATH_SPECIFIED=false

# 사용법 출력
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -u, --user USER       Remote user (default: ubuntu)"
    echo "  -h, --host HOST       Remote host (required)"
    echo "  -P, --port PORT       SSH port (default: 22)"
    echo "  -p, --path PATH       Remote path (default: /home/USER/wireless-simulation-pipeline)"
    echo "  --sync-only          Only sync code, don't deploy"
    echo "  --deploy-only        Only deploy, don't sync"
    echo "  --help               Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  REMOTE_USER          Remote user"
    echo "  REMOTE_HOST          Remote host"
    echo "  REMOTE_PORT          SSH port"
    echo "  REMOTE_PATH          Remote path"
    echo ""
    echo "Examples:"
    echo "  $0 -h 192.168.1.100"
    echo "  $0 -u myuser -h my-server.com -P 2222"
    echo "  $0 -u ubuntu -h my-server.com -P 2222 -p /opt/wireless-sim"
    echo "  REMOTE_HOST=my-server.com REMOTE_USER=myuser REMOTE_PORT=2222 $0"
    exit 1
}

# 인자 파싱
SYNC=true
DEPLOY=true

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
        -p|--path)
            REMOTE_PATH="$2"
            REMOTE_PATH_SPECIFIED=true
            shift 2
            ;;
        --sync-only)
            DEPLOY=false
            shift
            ;;
        --deploy-only)
            SYNC=false
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

# REMOTE_PATH 설정
# -p 옵션으로 명시적으로 지정하지 않았으면, REMOTE_USER의 홈 디렉토리 기반으로 자동 설정
# 이렇게 하면 사용자가 지정한 사용자의 홈 디렉토리에 자동으로 배포됨
if [ "$REMOTE_PATH_SPECIFIED" = false ]; then
    REMOTE_PATH="${REMOTE_PATH:-/home/$REMOTE_USER/wireless-simulation-pipeline}"
fi

echo "====================================="
echo "Remote Deployment Script"
echo "====================================="
echo "Remote Host: ${REMOTE_USER}@${REMOTE_HOST}"
echo "SSH Port: ${REMOTE_PORT}"
echo "Remote Path: ${REMOTE_PATH}"
if [ "$REMOTE_PATH_SPECIFIED" = false ]; then
    echo "         (auto-generated from user)"
fi
echo "====================================="
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 연결 테스트
echo "🔍 Testing connection to remote server..."
if ! ssh -p ${REMOTE_PORT} -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} "echo 'Connection successful'" > /dev/null 2>&1; then
    echo "❌ Failed to connect to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}"
    echo ""
    echo "Please check:"
    echo "  1. Server is running"
    echo "  2. SSH is accessible on port ${REMOTE_PORT}"
    echo "  3. User and host are correct"
    echo "  4. SSH key is set up (to avoid password prompts):"
    echo "     ssh-copy-id -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}"
    exit 1
fi
echo "✅ Connection successful"

# SSH 키 기반 인증 확인
if ssh -p ${REMOTE_PORT} -o BatchMode=yes -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} "echo 'OK'" > /dev/null 2>&1; then
    echo "✅ SSH key authentication configured (no password needed)"
else
    echo "⚠️  SSH key authentication not configured"
    echo "   You will be prompted for password multiple times"
    echo "   To set up SSH key: ssh-copy-id -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}"
fi
echo ""

# 코드 동기화
if [ "$SYNC" = true ]; then
    echo "📤 Syncing code to remote server..."
    
    # 원격 디렉토리 생성 (없는 경우)
    echo "📁 Ensuring remote directory exists..."
    ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_PATH}"
    
    # rsync가 있는지 확인
    if command -v rsync &> /dev/null; then
        rsync -avz --progress \
            -e "ssh -p ${REMOTE_PORT}" \
            --exclude='.git' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='*.pyo' \
            --exclude='*.tar' \
            --exclude='.DS_Store' \
            --exclude='*.swp' \
            --exclude='.vscode' \
            --exclude='custom' \
            . ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
    else
        echo "⚠️  rsync not found, using scp (slower)..."
        scp -P ${REMOTE_PORT} -r . ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
    fi
    
    echo "✅ Code synced"
    echo ""
fi

# 원격 배포
if [ "$DEPLOY" = true ]; then
    echo "🚀 Deploying on remote server..."
    echo ""
    
    ssh -p ${REMOTE_PORT} -t ${REMOTE_USER}@${REMOTE_HOST} bash << ENDSSH
set -e

cd ${REMOTE_PATH}

echo "====================================="
echo "Remote Server Deployment"
echo "====================================="
echo ""

# K3s 설치 확인
if ! command -v k3s &> /dev/null; then
    echo "K3s not found. Installing..."
    echo ""
    echo "⚠️  Note: K3s installation requires sudo permissions"
    echo "   If this fails, configure sudo NOPASSWD on the server:"
    echo "   1. SSH to server: ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}"
    echo "   2. Run: sudo visudo"
    echo "   3. Add: ${REMOTE_USER} ALL=(ALL) NOPASSWD: ALL"
    echo ""
    chmod +x scripts/install-k3s.sh
    ./scripts/install-k3s.sh
    
    # 환경변수 설정
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
    echo ""
else
    echo "✅ K3s is already installed"
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
    echo ""
fi

# 이미지 빌드
echo "🔨 Building Docker images..."
echo "ℹ️  Note: If sudo password is required, you may need to configure sudo NOPASSWD"
echo "   Run this on the server: sudo visudo"
echo "   Add: ${REMOTE_USER} ALL=(ALL) NOPASSWD: /usr/local/bin/k3s"
echo ""
chmod +x scripts/build-images.sh
./scripts/build-images.sh
echo ""

# 배포
echo "📦 Deploying to K3s..."
chmod +x scripts/deploy-all.sh
./scripts/deploy-all.sh
echo ""

echo "====================================="
echo "✅ Deployment Complete!"
echo "====================================="
echo ""

# 상태 확인
echo "📊 Current deployment status:"
kubectl get pods -A | grep -E "(NAMESPACE|queue-system|storage-pool|scenario-pool|calc-pool|monitor-pool|control-pool)"
echo ""

# 서비스 포트 확인
echo "🌐 Service ports:"
kubectl get svc -A | grep -E "(NAMESPACE|api-gateway|monitor-service)"
echo ""

ENDSSH
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "====================================="
        echo "✅ Remote Deployment Successful!"
        echo "====================================="
        echo ""
        echo "🌐 Access your application:"
        echo ""
        echo "Option 1: SSH Tunnel (Recommended)"
        echo "  - 서버 방화벽에서 30080, 30081, 30082 포트를 개방할 필요 없음"
        echo "  - SSH 포트만 열려있으면 됨 (보안상 권장)"
        echo "  - Run this command in a new terminal:"
        if [ "${REMOTE_PORT}" != "22" ]; then
            echo "  ssh -p ${REMOTE_PORT} -L 30080:localhost:30080 -L 30081:localhost:30081 -L 30082:localhost:30082 ${REMOTE_USER}@${REMOTE_HOST}"
        else
            echo "  ssh -L 30080:localhost:30080 -L 30081:localhost:30081 -L 30082:localhost:30082 ${REMOTE_USER}@${REMOTE_HOST}"
        fi
        echo ""
        echo "  Then access (터널이 유지되는 동안):"
        echo "  - API Gateway:     http://localhost:30080"
        echo "  - Monitor Service: http://localhost:30081"
        echo "  - WebSocket:       ws://localhost:30082"
        echo ""
        echo "Option 2: Direct Access (서버 방화벽에서 포트 개방 필요)"
        echo "  - 서버 방화벽에서 30080, 30081, 30082 포트를 외부에 개방해야 함"
        echo "  - API Gateway:     http://${REMOTE_HOST}:30080"
        echo "  - Monitor Service: http://${REMOTE_HOST}:30081"
        echo "  - WebSocket:       ws://${REMOTE_HOST}:30082"
        echo ""
        echo "💡 View logs:"
        if [ "${REMOTE_PORT}" != "22" ]; then
            echo "  ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} 'kubectl logs -n control-pool -l app=api-gateway -f'"
        else
            echo "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'kubectl logs -n control-pool -l app=api-gateway -f'"
        fi
        echo ""
        echo "💡 Check status:"
        if [ "${REMOTE_PORT}" != "22" ]; then
            echo "  ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} 'kubectl get pods -A'"
        else
            echo "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'kubectl get pods -A'"
        fi
        echo ""
    else
        echo ""
        echo "❌ Deployment failed on remote server"
        exit 1
    fi
else
    echo "✅ Sync complete (deploy skipped)"
fi

