# Wireless Simulation Pipeline - Project Structure

```text
wireless-simulation-pipeline/
│
├── README.md                           # 전체 프로젝트 문서
├── QUICKSTART.md                       # 빠른 시작 가이드
│
├── .devcontainer/                      # VS Code DevContainer 설정
│   ├── Dockerfile                      # 개발 환경 이미지
│   └── devcontainer.json               # DevContainer 설정
│
├── namespaces/                         # Kubernetes 네임스페이스
│   └── create-namespaces.yaml          # 6개 Pool 네임스페이스 정의
│
├── queue-system/                       # Redis Queue System
│   └── redis.yaml                      # Redis Deployment & Service
│
├── storage-pool/                       # Storage Pool (시뮬레이션 데이터 저장)
│   ├── storage-app.py                  # Flask API 서버
│   ├── Dockerfile                      # 이미지 빌드 파일
│   └── deployment.yaml                 # K8s Deployment & Service
│
├── scenario-pool/                      # Scenario Pool (시나리오 생성)
│   ├── scenario-app.py                 # Scenario Generator API
│   ├── Dockerfile
│   └── deployment.yaml
│
├── calc-pool/                          # Calc Pool (계산 워커들)
│   ├── system-core.py                  # 시뮬레이션 조율 워커
│   ├── channel-generator.py            # 채널 생성 워커
│   ├── pdp-interpolator.py             # PDP 보간 워커
│   ├── Dockerfile                      # 공통 이미지 (3개 워커 포함)
│   └── deployment.yaml                 # 3개의 Deployment
│
├── monitor-pool/                       # Monitor Pool (실시간 모니터링)
│   ├── monitor-service.py              # WebSocket 서버 + HTTP API
│   ├── Dockerfile
│   └── deployment.yaml                 # NodePort 서비스 (30081, 30082)
│
├── control-pool/                       # Control Pool (API Gateway)
│   ├── api-gateway.py                  # 통합 API Gateway
│   ├── Dockerfile
│   └── deployment.yaml                 # NodePort 서비스 (30080)
│
├── client/                             # 클라이언트 애플리케이션
│   ├── web-client.html                 # 웹 기반 모니터링 UI
│   └── blender-viewer.py               # Blender 3D 뷰어 샘플
│
├── monitoring/                         # 통합 모니터링 시스템
│   ├── namespace.yaml                  # monitoring 네임스페이스
│   ├── prometheus.yaml                 # Prometheus 설정 및 배포
│   ├── grafana.yaml                    # Grafana 설정 및 대시보드
│   └── kubernetes-dashboard.yaml       # Kubernetes Dashboard
│
└── scripts/                            # 자동화 스크립트
    ├── install-k3s.sh                  # K3s 설치
    ├── build-images.sh                 # Docker 이미지 빌드
    ├── deploy-all.sh                   # 전체 시스템 배포
    ├── deploy-monitoring.sh            # 모니터링 스택 배포
    ├── cleanup-monitoring.sh           # 모니터링 스택 정리
    ├── test-pipeline.sh                # 파이프라인 테스트
    ├── cleanup.sh                      # 리소스 정리
    └── uninstall-k3s.sh                # K3s 제거
```

## 주요 컴포넌트 설명

### Pool 구조

1. **Storage Pool**
   - 시뮬레이션 결과 및 시나리오 데이터 저장
   - Flask REST API
   - emptyDir 볼륨 사용 (영구 저장소로 확장 가능)

2. **Scenario Pool**
   - 시뮬레이션 시나리오 생성
   - 사용자 위치, 기지국 배치 등 생성
   - Storage Pool과 연동

3. **Calc Pool**
   - **System Core**: 전체 시뮬레이션 조율
   - **Channel Generator**: Ray Tracing 기반 채널 생성
   - **PDP Interpolator**: 전력 지연 프로파일 보간
   - Redis Queue를 통한 작업 분배

4. **Monitor Pool**
   - WebSocket 기반 실시간 모니터링
   - Delta Buffer를 통한 효율적 업데이트
   - HTTP API (8080) + WebSocket (8081)

5. **Control Pool**
   - API Gateway (모든 API 통합)
   - REST API 엔드포인트 제공
   - NodePort 30080으로 외부 노출

6. **Queue System**
   - Redis 기반 작업 큐
   - 비동기 작업 처리
   - 모든 Pool이 공유

### 통신 흐름

```text
Client
  ↓ (HTTP REST)
API Gateway (Control Pool)
  ↓
  ├→ Scenario Pool → Storage Pool
  ├→ Simulation Queue (Redis)
  └→ Monitor Service
      ↑ (WebSocket)
    Client

Simulation Queue
  ↓
System Core (Calc Pool)
  ↓
  ├→ Channel Queue → Channel Generator
  └→ PDP Queue → PDP Interpolator
      ↓
Monitor Update Queue
  ↓
Monitor Service → Client (WebSocket)
```

### 포트 맵핑

| 서비스               | 내부 포트 | NodePort | 용도          |
| -------------------- | --------- | -------- | ------------- |
| API Gateway          | 8080      | 30080    | REST API      |
| Monitor HTTP         | 8080      | 30081    | HTTP API      |
| Monitor WebSocket    | 8081      | 30082    | WebSocket     |
| Prometheus           | 9090      | 30090    | 메트릭 수집   |
| Grafana              | 3000      | 30091    | 대시보드      |
| Kubernetes Dashboard | 9090      | 30092    | 클러스터 관리 |

### 환경 변수

모든 서비스가 공통으로 사용하는 환경 변수:

- `REDIS_HOST`: redis-service.queue-system.svc.cluster.local
- `REDIS_PORT`: 6379

각 서비스별 Storage Service URL:

- `STORAGE_SERVICE_URL`: <http://storage-service.storage-pool.svc.cluster.local:8080>

## 데이터 흐름

1. **시나리오 생성**

   ```text
   Client → API Gateway → Scenario Pool → Storage Pool
   ```

2. **시뮬레이션 시작**

   ```text
   Client → API Gateway → Simulation Queue
   → System Core → Channel Queue / PDP Queue
   → Workers → Monitor Update Queue
   → Monitor Service → Client (WebSocket)
   ```

3. **결과 조회**

   ```text
   Client → API Gateway → Storage Pool
   ```

## 확장성

- **Horizontal Scaling**: Worker replica 수 증가
- **Vertical Scaling**: Resource limits 증가
- **Storage**: emptyDir → PersistentVolume 변경
- **Redis**: Cluster 모드로 확장
- **GPU**: calc-pool에 GPU 할당

## 모니터링 (Monitoring Stack)

프로젝트에는 통합 모니터링 시스템이 포함되어 있습니다.

### 구성 요소

1. **Prometheus** (포트 30090)
   - 메트릭 수집 및 저장
   - Kubernetes 서비스 자동 검색
   - 15일 데이터 보존

2. **Grafana** (포트 30091)
   - 시각화 대시보드
   - 사전 구성된 대시보드:
     - Wireless Simulation Pipeline
     - Kubernetes Cluster
   - 기본 로그인: admin / admin123

3. **Kubernetes Dashboard** (포트 30092)
   - 클러스터 리소스 관리
   - Pod/Deployment 상태 모니터링
   - 실시간 로그 확인

### 포트 맵핑 (모니터링)

| 서비스               | 내부 포트 | NodePort | 용도          |
| -------------------- | --------- | -------- | ------------- |
| Prometheus           | 9090      | 30090    | 메트릭 수집   |
| Grafana              | 3000      | 30091    | 대시보드      |
| Kubernetes Dashboard | 9090      | 30092    | 클러스터 관리 |

### 배포 명령어

```bash
# 모니터링 스택 배포
./scripts/deploy-monitoring.sh

# 모니터링 스택 정리
./scripts/cleanup-monitoring.sh

# Dashboard 토큰 확인
kubectl get secret admin-user-token -n kubernetes-dashboard -o jsonpath='{.data.token}' | base64 -d && echo
```

### 추가 확장 가능

- Loki + Promtail로 로그 수집 가능
- AlertManager로 알림 설정 가능
- Jaeger/Zipkin으로 분산 트레이싱 가능
