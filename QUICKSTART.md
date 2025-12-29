# Wireless Simulation Pipeline - Quick Start Guide

## 🚀 빠른 시작 (5분 안에 실행하기)

### 전제 조건

- Linux 환경 (Ubuntu 20.04+)
- Docker 설치됨
- sudo 권한
- 최소 8GB RAM

### 1단계: K3s 설치

```bash
cd wireless-simulation-pipeline
./scripts/install-k3s.sh

# 환경변수 적용
source ~/.bashrc
```

### 2단계: Docker 이미지 빌드

```bash
./scripts/build-images.sh
```

⏱️ 예상 시간: 3-5분

### 3단계: 전체 시스템 배포

```bash
./scripts/deploy-all.sh
```

⏱️ 예상 시간: 2-3분

### 4단계: 시스템 테스트

```bash
./scripts/test-pipeline.sh
```

### 5단계: 웹 클라이언트 열기

**방법 1**: 웹 서버를 통한 접근 (권장)

브라우저에서 다음 URL을 엽니다:

```text
http://localhost:30080/web_client
```

또는 터미널에서:

```bash
# Chrome/Chromium이 설치되어 있는 경우
google-chrome http://localhost:30080/web_client

# Firefox가 설치되어 있는 경우
firefox http://localhost:30080/web_client
```

**방법 2**: 파일 직접 열기 (로컬 개발용)

```bash
# Chrome/Chromium이 설치되어 있는 경우
google-chrome client/web-client.html

# Firefox가 설치되어 있는 경우
firefox client/web-client.html
```

## 📊 API 엔드포인트

기본적으로 다음 포트에서 서비스가 실행됩니다:

- **웹 클라이언트**: <http://localhost:30080/web_client>
- **API Gateway**: <http://localhost:30080/api>
- **WebSocket (Monitor)**: ws://localhost:30082

### 주요 API

#### 1. 시나리오 생성

```bash
curl -X POST http://localhost:30080/api/scenario/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Scenario",
    "num_users": 10,
    "duration": 60
  }'
```

#### 2. 시뮬레이션 시작

```bash
curl -X POST http://localhost:30080/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "scenario_xxxxx"}'
```

#### 3. 상태 확인

```bash
curl http://localhost:30080/api/simulation/status/sim_xxxxx
```

#### 4. 큐 통계

```bash
curl http://localhost:30080/api/queue/stats
```

## 🔍 문제 해결

### Pod 상태 확인

```bash
kubectl get pods -A
```

### 로그 확인

```bash
# API Gateway 로그
kubectl logs -n control-pool -l app=api-gateway

# Monitor Service 로그
kubectl logs -n monitor-pool -l app=monitor-service

# Worker 로그
kubectl logs -n calc-pool -l app=system-core
kubectl logs -n calc-pool -l app=channel-generator
kubectl logs -n calc-pool -l app=pdp-interpolator
```

### Redis 연결 확인

```bash
kubectl exec -n queue-system deployment/redis -- redis-cli ping
```

### 서비스 재시작

```bash
# 특정 deployment 재시작
kubectl rollout restart deployment/api-gateway -n control-pool

# 모든 서비스 재배포
./scripts/cleanup.sh
./scripts/deploy-all.sh
```

## 🧹 정리

### 배포된 리소스만 삭제

```bash
./scripts/cleanup.sh
```

### K3s 완전 제거

```bash
./scripts/uninstall-k3s.sh
```

## 📚 다음 단계

1. **웹 클라이언트 사용**: `http://localhost:30080/web_client`에서 실시간 모니터링
2. **Blender 통합**: `client/blender-viewer.py`를 참고하여 3D 시각화
3. **커스텀 시나리오**: 다양한 파라미터로 시나리오 생성
4. **성능 테스트**: 더 많은 사용자와 더 긴 시뮬레이션으로 테스트

## 💡 팁

- 웹 클라이언트는 WebSocket이 자동 연결됩니다
- 시뮬레이션 ID를 저장해두면 나중에 결과 조회 가능
- Pod가 준비되는 데 시간이 걸릴 수 있습니다 (최대 1-2분)
- 리소스가 부족하면 replica 수를 줄여보세요

## 🐛 알려진 이슈

1. **WebSocket 연결 실패**: Monitor Service Pod가 완전히 준비될 때까지 기다려주세요
2. **이미지 빌드 실패**: Docker daemon이 실행 중인지 확인
3. **Pod가 Pending 상태**: `kubectl describe pod <pod-name> -n <namespace>`로 상세 확인

## 📖 전체 문서

자세한 내용은 `README.md`를 참조하세요.
