# Wireless Simulation Pipeline - 통합 모니터링 가이드

이 문서는 Prometheus, Grafana, Kubernetes Dashboard를 사용한 통합 모니터링 시스템 설정 및 사용 방법을 설명합니다.

## 아키텍처

```text
┌─────────────────────────────────────────────────────────────────┐
│                      Monitoring Stack                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │  Prometheus  │───▶│   Grafana    │    │ K8s Dashboard     │  │
│  │  :30090      │    │   :30091     │    │     :30092        │  │
│  └──────┬───────┘    └──────────────┘    └───────────────────┘  │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Kubernetes Cluster Metrics                  │   │
│  │  • control-pool  • scenario-pool  • calc-pool            │   │
│  │  • monitor-pool  • storage-pool   • queue-system         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 빠른 시작

### 1. 로컬 배포

```bash
./scripts/deploy-monitoring.sh
```

### 2. 원격 서버 배포

```bash
# 메인 서비스와 함께 모니터링 배포
./scripts/deploy-to-remote.sh -h <server-ip> --with-monitoring

# 모니터링만 배포
./scripts/deploy-to-remote.sh -h <server-ip> --monitoring-only
```

### 3. 접속 URL

| 서비스               | URL                      | 설명                |
| -------------------- | ------------------------ | ------------------- |
| Prometheus           | <http://localhost:30090> | 메트릭 쿼리 및 확인 |
| Grafana              | <http://localhost:30091> | 시각화 대시보드     |
| Kubernetes Dashboard | <http://localhost:30092> | 클러스터 관리       |

### 4. 원격 서버 접속 (SSH 터널)

원격 서버에 배포한 경우, SSH 터널을 통해 접속합니다:

```bash
# SSH 터널 생성 (새 터미널에서 실행)
ssh -L 30090:localhost:30090 -L 30091:localhost:30091 -L 30092:localhost:30092 user@server-ip

# 커스텀 SSH 포트 사용 시
ssh -p 2222 -L 30090:localhost:30090 -L 30091:localhost:30091 -L 30092:localhost:30092 user@server-ip
```

터널이 유지되는 동안 위의 localhost URL로 접속 가능합니다.

### 3. 기본 로그인 정보

**Grafana:**

- Username: `admin`
- Password: `admin123`

**Kubernetes Dashboard:**

```bash
# 토큰 확인
kubectl get secret admin-user-token -n kubernetes-dashboard -o jsonpath='{.data.token}' | base64 -d && echo
```

## Prometheus

### 주요 기능

- **자동 서비스 검색**: Kubernetes 서비스 자동 검색 및 메트릭 수집
- **메트릭 저장**: 15일간 메트릭 데이터 보존
- **쿼리 인터페이스**: PromQL을 통한 메트릭 쿼리

### 수집 대상

1. **Kubernetes 시스템**
   - API Server
   - Node 메트릭
   - cAdvisor (컨테이너 메트릭)

2. **Wireless Simulation Pipeline 서비스**
   - control-pool (API Gateway)
   - scenario-pool (Scenario Service)
   - calc-pool (System Core, Channel Generator, PDP Interpolator)
   - monitor-pool (Monitor Service)
   - storage-pool (Storage Service)
   - queue-system (Redis)

### 유용한 PromQL 쿼리

```promql
# 전체 Pod 수
count(kube_pod_info{namespace=~"control-pool|scenario-pool|calc-pool|monitor-pool|storage-pool|queue-system"})

# 네임스페이스별 메모리 사용량
sum(container_memory_usage_bytes{namespace=~"control-pool|scenario-pool|calc-pool|monitor-pool|storage-pool|queue-system"}) by (namespace)

# 네임스페이스별 CPU 사용률
sum(rate(container_cpu_usage_seconds_total{namespace=~"control-pool|scenario-pool|calc-pool|monitor-pool|storage-pool|queue-system"}[5m])) by (namespace) * 100

# 서비스 상태 확인
up{job="wireless-simulation-services"}
```

## Grafana

### 사전 구성된 대시보드

#### 1. Wireless Simulation Pipeline

- **위치**: Dashboards > Browse > Wireless Simulation Pipeline
- **패널**:
  - Cluster Overview (Total Pods, Services Up, CPU/Memory Usage)
  - Memory/CPU Usage by Pool
  - Network I/O by Pool
  - CPU Throttling
  - Service Status

#### 2. Kubernetes Cluster

- **위치**: Dashboards > Browse > Kubernetes Cluster
- **패널**:
  - Cluster CPU/Memory/Disk Usage
  - CPU Usage by Mode
  - Memory Usage Trend

### 커스텀 대시보드 생성

1. Grafana 접속 (<http://localhost:30091>)
2. 좌측 메뉴 > Dashboards > New Dashboard
3. Add visualization 클릭
4. Prometheus 데이터소스 선택
5. PromQL 쿼리 입력

### 알림 설정 (선택사항)

```yaml
# Grafana에서 알림 채널 설정 (Settings > Alerting > Contact points)
# Slack, Email, PagerDuty 등 지원
```

## Kubernetes Dashboard

### KD 주요 기능

- **클러스터 개요**: 노드, 네임스페이스, 워크로드 상태
- **워크로드 관리**: Deployment, Pod, Service 관리
- **로그 확인**: Pod 실시간 로그
- **Shell 접속**: 컨테이너 내부 접속

### 사용 방법

1. <http://localhost:30092> 접속
2. "Skip" 버튼 클릭 (또는 토큰 입력)
3. 네임스페이스 선택하여 리소스 확인

### 네임스페이스별 리소스 확인

- **control-pool**: API Gateway
- **scenario-pool**: Scenario Service
- **calc-pool**: System Core, Channel Generator, PDP Interpolator
- **monitor-pool**: Monitor Service
- **storage-pool**: Storage Service
- **queue-system**: Redis

## 문제 해결

### Pod 상태 확인

```bash
# 모니터링 Pod 상태
kubectl get pods -n monitoring
kubectl get pods -n kubernetes-dashboard

# Pod 로그 확인
kubectl logs -n monitoring -l app=prometheus
kubectl logs -n monitoring -l app=grafana
kubectl logs -n kubernetes-dashboard -l app=kubernetes-dashboard
```

### Prometheus 타겟 확인

1. <http://localhost:30090> 접속
2. Status > Targets 메뉴
3. 모든 타겟이 "UP" 상태인지 확인

### Grafana 데이터소스 확인

1. <http://localhost:30091> 접속
2. Configuration > Data sources
3. Prometheus 데이터소스가 "Working" 상태인지 확인

### 일반적인 문제

| 문제                 | 원인          | 해결 방법                             |
| -------------------- | ------------- | ------------------------------------- |
| Prometheus 타겟 DOWN | 서비스 미배포 | `./scripts/deploy-all.sh` 실행        |
| Grafana 접속 불가    | Pod 시작 중   | `kubectl get pods -n monitoring` 확인 |
| Dashboard 빈 데이터  | 메트릭 미수집 | Prometheus 타겟 상태 확인             |

## 모니터링 스택 제거

```bash
./scripts/cleanup-monitoring.sh
```

## 확장 옵션

### Loki (로그 수집)

```yaml
# 향후 추가 가능
# - Loki: 로그 집계 서버
# - Promtail: 로그 수집 에이전트
```

### AlertManager (알림)

```yaml
# 향후 추가 가능
# - Slack, Email, PagerDuty 연동
# - 커스텀 알림 규칙 설정
```

### Jaeger (분산 트레이싱)

```yaml
# 향후 추가 가능
# - 서비스 간 호출 추적
# - 지연 시간 분석
```
