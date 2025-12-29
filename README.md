# Wireless Simulation Pipeline - K3s Sample Project

AI-Native Upper-mid band E-MIMO 프로젝트의 무선 통신 시뮬레이션 시스템 샘플 구현

## 🎯 프로젝트 개요

### 목적

단일 서버에서 무선 통신 시뮬레이션 시스템의 핵심 아키텍처를 K3s로 구현한 교육/테스트용 샘플 프로젝트

### 주요 기능

- ✅ **Scenario Pool**: 시뮬레이션 시나리오 관리 및 생성
- ✅ **Control Pool**: API Gateway를 통한 시스템 제어
- ✅ **Calc Pool**: Channel Generator, PDP Interpolator, System Core
- ✅ **Monitor Pool**: 3D Monitor Service, Delta 기반 실시간 업데이트
- ✅ **Storage Pool**: 시뮬레이션 결과 저장 및 조회
- ✅ **WebSocket**: Monitor Pool ↔ 클라이언트 실시간 통신
- ✅ **Queue System**: Redis 기반 비동기 작업 처리

## 시스템 아키텍처

### Pool 구조

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │  Web Client      │◄─WebSocket──►│ Blender 3D       │         │
│  │  (Browser)       │              │ Viewer           │         │
│  └──────────────────┘              └──────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Control Pool                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Gateway                           │   │
│  │              (REST API + WebSocket Proxy)                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│ Scenario     │    │   Calc        │    │   Monitor    │
│   Pool       │    │   Pool        │    │    Pool      │
│              │    │               │    │              │
│ - Scenario   │    │ - System      │    │ - 3D Monitor │
│   Generator  │    │   Core        │    │   Service    │
│ - Registry   │    │ - Channel     │    │ - Delta      │
│              │    │   Generator   │    │   Buffer     │
│              │    │ - PDP         │    │              │
│              │    │   Interpolator│    │              │
└──────────────┘    └───────────────┘    └──────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
                    ┌──────────────┐
                    │   Storage    │
                    │    Pool      │
                    │              │
                    │ - MinIO      │
                    │ - Results DB │
                    └──────────────┘
                              │
                              ▼
                    ┌──────────────┐
                    │Queue System  │
                    │   (Redis)    │
                    └──────────────┘
```

## 📂 프로젝트 구조

```text
wireless-simulation-pipeline/
├── .devcontainer/
│   ├── devcontainer.json               # VS Code DevContainer 설정
│   └── Dockerfile                      # 개발 환경 이미지
├── namespaces/
│   └── create-namespaces.yaml          # K3s 네임스페이스
├── queue-system/
│   └── redis.yaml                      # Redis 배포
├── storage-pool/
│   ├── storage-app.py                  # Storage API
│   ├── Dockerfile
│   └── deployment.yaml
├── scenario-pool/
│   ├── scenario-app.py                 # Scenario Generator API
│   ├── Dockerfile
│   └── deployment.yaml
├── calc-pool/
│   ├── system-core.py                  # System Core Worker
│   ├── channel-generator.py            # Channel Generator
│   ├── pdp-interpolator.py             # PDP Interpolator
│   ├── Dockerfile
│   └── deployment.yaml
├── monitor-pool/
│   ├── monitor-service.py              # 3D Monitor Service (WebSocket)
│   ├── Dockerfile
│   └── deployment.yaml
├── control-pool/
│   ├── api-gateway.py                  # API Gateway (REST + WebSocket Proxy)
│   ├── Dockerfile
│   └── deployment.yaml
├── client/
│   ├── web-client.html                 # 웹 클라이언트 (WebSocket)
│   └── blender-viewer.py               # Blender 3D Viewer 샘플
├── scripts/
│   ├── install-k3s.sh                # K3s 설치
│   ├── build-images.sh               # 이미지 빌드
│   ├── deploy-all.sh                 # K3s 배포
│   ├── deploy-to-remote.sh           # 원격 서버 배포
│   ├── setup-remote-kubectl.sh       # 원격 kubectl 설정
│   ├── test-pipeline.sh
│   ├── cleanup.sh
│   └── uninstall-k3s.sh
├── custom/
│   └── .gitignore                    # 사용자 전용 폴더 (내용은 Git 무시)
│   └── commands.md                   # 개인 전용 명령어 모음 (예시)
├── REMOTE-DEPLOYMENT.md              # 원격 배포 가이드
└── README.md
```

## 🚀 빠른 시작

### 사전 요구사항

- Linux 환경 (Ubuntu 20.04+)
- Docker 설치
- 최소 8GB RAM
- VS Code + Remote Containers 확장 (선택사항)

> 💡 **Mac/Windows에서 개발 중이신가요?**  
> 별도의 Ubuntu 서버에 배포하는 방법: **[원격 배포 가이드](./REMOTE-DEPLOYMENT.md)**

### 1. DevContainer로 개발 환경 시작 (선택)

```bash
# VS Code에서 프로젝트 열기
code wireless-simulation-pipeline/

# Command Palette (Ctrl+Shift+P)
# "Dev Containers: Reopen in Container" 선택
```

### 2. K3s 설치 및 배포

```bash
# 실행 권한 부여
chmod +x scripts/*.sh

# K3s 설치
./scripts/install-k3s.sh

# Docker 이미지 빌드
./scripts/build-images.sh

# 전체 시스템 배포
./scripts/deploy-all.sh
```

### 3. 시스템 테스트

```bash
# 파이프라인 테스트
./scripts/test-pipeline.sh
```

---

## 🌐 원격 Ubuntu 서버에 배포하기

로컬에서 개발하고, 별도의 Ubuntu 서버에 배포하는 워크플로우:

### 빠른 배포

```bash
# 로컬에서 실행
./scripts/deploy-to-remote.sh -h <ubuntu-server-ip>

# 예시
./scripts/deploy-to-remote.sh -h 192.168.1.100
./scripts/deploy-to-remote.sh -u ubuntu -h my-server.com
./scripts/deploy-to-remote.sh -h my-server.com -P 2222  # SSH 포트 지정

# 특정 풀만 캐시 없이 재빌드 (변경사항 확실히 반영)
./scripts/deploy-to-remote.sh -h my-server.com --no-cache control-pool calc-pool
```

**스크립트가 자동으로 수행:**

- ✅ 코드 동기화 (rsync)
- ✅ K3s 설치 확인
- ✅ Docker 이미지 빌드
- ✅ K3s에 배포

### 원격 클러스터 제어 (선택)

로컬 kubectl로 원격 서버의 K3s 클러스터를 제어할 수 있습니다.

```bash
# 방법 1: 직접 접속 (서버 6443 포트 개방 필요)
./scripts/setup-remote-kubectl.sh -h <ubuntu-server-ip>

# 방법 2: SSH 터널 사용 (권장, 6443 포트 개방 불필요)
./scripts/setup-remote-kubectl.sh -h <ubuntu-server-ip> --tunnel
# 별도 터미널에서 SSH 터널 유지:
# ssh -L 6443:localhost:6443 user@server-ip

# 이제 로컬에서 원격 클러스터 제어 가능
kubectl get pods -A
kubectl logs -n control-pool -l app=api-gateway -f
```

### 애플리케이션 접속

```bash
# SSH 터널 생성 (추천)
# - 서버 방화벽에서 30080, 30081, 30082 포트를 개방할 필요 없음
# - SSH 포트만 열려있으면 됨 (보안상 권장)
ssh -L 30080:localhost:30080 \
    -L 30081:localhost:30081 \
    -L 30082:localhost:30082 \
    ubuntu@<server-ip>

# SSH 포트가 다른 경우
ssh -p 2222 -L 30080:localhost:30080 \
    -L 30081:localhost:30081 \
    -L 30082:localhost:30082 \
    ubuntu@<server-ip>

# 브라우저에서 접속 (터널이 유지되는 동안)
# http://localhost:30080
# http://localhost:30081
# ws://localhost:30082
```

**📘 자세한 내용**: [원격 배포 가이드](./REMOTE-DEPLOYMENT.md)

> 💡 **향후 계획**: GitHub Actions를 통한 자동 배포 (현재는 수동 배포)

## 🧪 주요 시나리오 테스트

### 1. 시나리오 생성 및 시뮬레이션 시작

```bash
# API Gateway 주소 확인
NODE_PORT=$(kubectl get svc api-gateway -n control-pool -o jsonpath='{.spec.ports[0].nodePort}')
API_URL="http://localhost:$NODE_PORT"

# 새 시나리오 생성
curl -X POST $API_URL/api/scenario/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "urban_mobility",
    "num_users": 10,
    "area_size": [1000, 1000],
    "duration": 60
  }'

# 시뮬레이션 시작
curl -X POST $API_URL/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "<scenario_id>"}'
```

### 2. WebSocket 실시간 모니터링

```bash
# WebSocket 포트 확인
WS_PORT=$(kubectl get svc monitor-service -n monitor-pool -o jsonpath='{.spec.ports[1].nodePort}')

# 웹 브라우저에서 접속
# ws://localhost:$WS_PORT/ws
```

### 3. 계산 결과 조회

```bash
# 시뮬레이션 상태 확인
curl $API_URL/api/simulation/status/<simulation_id>

# 결과 다운로드
curl $API_URL/api/results/<simulation_id> -o results.json
```

## 📊 모니터링

### Pod 상태 확인

```bash
kubectl get pods -A
```

### 로그 확인

```bash
# API Gateway 로그
kubectl logs -n control-pool -l app=api-gateway -f

# Monitor Service 로그
kubectl logs -n monitor-pool -l app=monitor-service -f

# Calc Workers 로그
kubectl logs -n calc-pool -l app=calc-worker -f
```

### Queue 상태 확인

```bash
kubectl exec -n queue-system deployment/redis -- redis-cli llen simulation_queue
kubectl exec -n queue-system deployment/redis -- redis-cli llen channel_queue
kubectl exec -n queue-system deployment/redis -- redis-cli llen pdp_queue
```

## 🔧 개발 가이드

### 로컬 개발

각 Pool의 서비스는 독립적으로 개발 및 테스트 가능합니다.

```bash
# 예: Monitor Service 로컬 실행
cd monitor-pool
python monitor-service.py
```

### 이미지 재빌드

```bash
# 특정 서비스만 재빌드
docker build -t monitor-pool:latest ./monitor-pool
sudo k3s ctr images import monitor-pool.tar

# 또는 전체 재빌드
./scripts/build-images.sh
```

## 📚 API 문서

### Control Pool (API Gateway)

#### REST API Endpoints

- **시나리오 관리**
  - `POST /api/scenario/create` - 새 시나리오 생성
  - `GET /api/scenario/list` - 시나리오 목록
  - `GET /api/scenario/<id>` - 시나리오 상세정보
- **시뮬레이션 제어**
  - `POST /api/simulation/start` - 시뮬레이션 시작
  - `POST /api/simulation/stop` - 시뮬레이션 중지
  - `GET /api/simulation/status/<id>` - 시뮬레이션 상태
- **결과 조회**
  - `GET /api/results/<id>` - 결과 다운로드
  - `GET /api/results/list` - 결과 목록

#### WebSocket Proxy

- `WS /ws` - Monitor Service WebSocket 연결 프록시

### Monitor Pool

#### WebSocket Protocol

```json
// 클라이언트 → 서버: 구독
{
  "type": "subscribe",
  "simulation_id": "sim-123"
}

// 서버 → 클라이언트: Delta 업데이트
{
  "type": "delta_update",
  "simulation_id": "sim-123",
  "timestamp": 1234567890,
  "delta": {
    "ui_positions": [...],
    "material_states": [...]
  }
}

// 서버 → 클라이언트: Full Update (초기화)
{
  "type": "full_update",
  "simulation_id": "sim-123",
  "data": {
    "users": [...],
    "environment": {...}
  }
}
```

## 🧹 정리

### 배포 리소스 삭제

```bash
./scripts/cleanup.sh
```

### K3s 완전 제거

```bash
./scripts/uninstall-k3s.sh
```

## 📖 참고 자료

### 프로젝트 문서

- **[🚀 원격 배포 가이드](./REMOTE-DEPLOYMENT.md)** - Mac/로컬에서 개발 후 Ubuntu 서버에 배포

### 외부 자료

- [K3s 공식 문서](https://docs.k3s.io/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- [Redis Queue](https://python-rq.org/)

## 🎓 학습 목표

이 샘플 프로젝트를 통해 다음을 학습할 수 있습니다:

1. **K3s 기반 마이크로서비스 아키텍처**
2. **Pool 기반 논리적 시스템 분리**
3. **REST API와 WebSocket의 하이브리드 통신**
4. **Redis Queue를 통한 비동기 작업 처리**
5. **Delta 기반 실시간 데이터 전송 최적화**
6. **무선 통신 시뮬레이션 워크플로우**
