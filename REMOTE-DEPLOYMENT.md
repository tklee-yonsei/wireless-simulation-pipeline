# 원격 Ubuntu 서버에 배포하기

로컬(Mac/Windows)에서 개발하고, 별도의 Ubuntu 서버에 K3s를 배포하는 가이드입니다.

---

## 🎯 개발 워크플로우

```text
┌─────────────────┐           ┌──────────────────────┐
│  Local Dev Env  │  SSH/SCP  │  Ubuntu Server       │
│                 │ ────────► │  (K3s Runtime)       │
│ - Code Dev      │           │  - K3s Cluster       │
│ - Unit Tests    │           │  - Production Env    │
│ - kubectl Ctrl  │           │  - RTX 3090 GPU      │
└─────────────────┘           │  - 64GB RAM          │
                              └──────────────────────┘
```

### 워크플로우

1. **로컬에서 개발**: 코드 작성 및 유닛테스트
2. **서버로 배포**: `deploy-to-remote.sh` 스크립트 사용
3. **서버에서 실제 테스트**: K3s 환경에서 통합 테스트
4. **모니터링**: 로컬에서 kubectl로 원격 클러스터 제어

> 💡 **향후 계획**: GitHub Actions를 통한 자동 배포 (현재는 수동 배포)

---

## 📋 사전 준비

### Ubuntu 서버 요구사항

- **운영체제**: Ubuntu 20.04 이상
- **메모리**: 64GB RAM ✅
- **GPU**: RTX 3090 ✅
- **스토리지**: 50GB 이상 여유 공간 (권장)
- **네트워크**: SSH 접근 가능 (기본 포트 22 또는 사용자 지정 포트)
- **sudo 권한**: ⭐ **필수** - 원격 배포 시 sudo NOPASSWD 설정 필요
- **방화벽**:
  - SSH 포트는 필수 (기본 22 또는 사용자 지정)
  - 6443 포트: kubectl 원격 제어 시 필요 (선택)
  - 30080-30082 포트: SSH 터널링 사용 시 개방 불필요 (직접 접속 시에만 필요)

### 사전 설정 (서버에서 한 번만 실행)

**⚠️ 중요**: 원격 배포 스크립트가 작동하려면 서버에서 다음 설정이 필요합니다:

#### 1. sudo NOPASSWD 설정 (필수)

```bash
# 서버에 SSH 접속
ssh user@server-ip

# sudoers 파일 편집
sudo visudo
```

**파일에서 추가할 위치**:

`visudo`로 열린 `/etc/sudoers` 파일에서:

- 파일 끝 부분(마지막 줄 근처)에 다음 줄 추가:

  ```text
  user ALL=(ALL) NOPASSWD: ALL
  ```

- 또는 더 제한적으로 (보안상 권장):
  
  ```text
  user ALL=(ALL) NOPASSWD: /usr/local/bin/k3s, /usr/bin/systemctl, /usr/local/bin/k3s-uninstall.sh
  ```

- `user`를 실제 사용자명으로 변경 (예: `ubuntu`, `myuser` 등)
- 저장: `:wq` (vi) 또는 `Ctrl+X` → `Y` → `Enter` (nano)

**예시 위치** (파일 끝 부분):

```text
# Allow members of group sudo to execute any command
%sudo   ALL=(ALL:ALL) ALL

# 여기에 추가
user ALL=(ALL) NOPASSWD: ALL
```

**또는 별도 파일로 추가 (권장)**:

```bash
sudo visudo -f /etc/sudoers.d/k3s-user
# 위 내용 추가 후 저장
```

**왜 필요한가?**

- 원격 배포 시 비대화형 SSH 세션에서 실행되므로 sudo 비밀번호를 입력할 수 없음
- k3s 설치 및 이미지 import 시 sudo 권한이 필요함

### 로컬 개발 환경 요구사항

- Docker Desktop (또는 Docker)
- SSH 클라이언트
- kubectl (원격 제어용, 선택사항)

---

## 🚀 배포 방법

### 자동 배포 스크립트 사용 (⭐ 추천)

한 번의 명령으로 코드 동기화 + 빌드 + 배포

```bash
# 로컬에서 실행
cd wireless-simulation-pipeline

# 기본 사용법
./scripts/deploy-to-remote.sh -h <ubuntu-server-ip>

# 예시
./scripts/deploy-to-remote.sh -h 192.168.1.100
./scripts/deploy-to-remote.sh -u ubuntu -h my-server.com
./scripts/deploy-to-remote.sh -h my-server.com -P 2222  # SSH 포트 지정

# 환경변수로 설정
export REMOTE_HOST=my-server.com
export REMOTE_USER=ubuntu
export REMOTE_PORT=2222  # SSH 포트 (기본값: 22)
./scripts/deploy-to-remote.sh
```

**스크립트가 자동으로 수행하는 작업:**

1. ✅ 코드를 서버로 동기화 (rsync)
2. ✅ K3s 설치 확인 (없으면 설치)
3. ✅ Docker 이미지 빌드
4. ✅ K3s에 배포
5. ✅ 배포 상태 확인

### 옵션

```bash
# 코드만 동기화 (배포 안 함)
./scripts/deploy-to-remote.sh -h <server> --sync-only

# 배포만 실행 (동기화 안 함)
./scripts/deploy-to-remote.sh -h <server> --deploy-only

# 특정 풀만 캐시 없이 재빌드 (변경사항 확실히 반영)
./scripts/deploy-to-remote.sh -h <server> --no-cache control-pool calc-pool

# 사용 가능한 풀 이름:
# - storage-pool
# - scenario-pool
# - calc-pool
# - monitor-pool
# - control-pool
```

---

## 🔧 수동 배포 (참고용)

스크립트 없이 수동으로 배포하려면:

### Step 1: 코드를 서버로 전송

```bash
# 로컬에서 실행
cd wireless-simulation-pipeline

# rsync로 전송 (추천 - 변경된 파일만 전송)
rsync -avz -e "ssh" --exclude='.git' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.DS_Store' \
  . ubuntu@server-ip:/home/ubuntu/wireless-simulation-pipeline/

# SSH 포트가 다른 경우
rsync -avz -e "ssh -p 2222" --exclude='.git' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.DS_Store' \
  . ubuntu@server-ip:/home/ubuntu/wireless-simulation-pipeline/
```

### Step 2: 서버에서 배포

```bash
# 서버에 SSH 접속
ssh ubuntu@server-ip

# 프로젝트 디렉토리로 이동
cd /home/ubuntu/wireless-simulation-pipeline

# K3s 설치 (처음 한 번만)
chmod +x scripts/*.sh
./scripts/install-k3s.sh

# 이미지 빌드 및 배포
./scripts/build-images.sh
./scripts/deploy-all.sh

# 상태 확인
kubectl get pods -A
```

---

## 🎮 로컬에서 원격 클러스터 제어

### kubectl 설정

이 스크립트는 로컬 kubectl로 원격 서버의 K3s 클러스터를 제어할 수 있도록 설정합니다.

**동작 방식:**

1. 원격 서버에서 kubeconfig 파일 다운로드 (SSH 사용)
2. 서버 주소 변경: `127.0.0.1` → 실제 서버 IP (또는 localhost for tunnel)
3. 로컬 kubectl 설정에 추가

**포트 요구사항:**

- **직접 접속 모드**: 서버의 6443 포트가 열려 있어야 함
- **SSH 터널 모드**: 6443 포트 개방 불필요 (SSH 터널 사용)

```bash
# 방법 1: 직접 접속 (서버 6443 포트 개방 필요)
./scripts/setup-remote-kubectl.sh -h <ubuntu-server-ip>

# 방법 2: SSH 터널 사용 (권장, 6443 포트 개방 불필요)
./scripts/setup-remote-kubectl.sh -h <ubuntu-server-ip> --tunnel
# 별도 터미널에서 SSH 터널 유지:
# ssh -L 6443:localhost:6443 user@server-ip

# SSH 포트가 다른 경우
./scripts/setup-remote-kubectl.sh -h <ubuntu-server-ip> -P 8027 --tunnel

# 이제 로컬에서 원격 클러스터를 직접 제어 가능!
kubectl get pods -A
kubectl logs -n control-pool -l app=api-gateway -f
kubectl describe pod -n calc-pool system-core-xxx
```

### Context 전환

```bash
# 사용 가능한 context 확인
kubectl config get-contexts

# 원격 서버 context로 전환
kubectl config use-context remote-k3s
```

---

## 🌐 애플리케이션 접속

### 방법 1: SSH 터널링 (추천)

**장점:**

- 서버 방화벽에서 30080, 30081, 30082 포트를 개방할 필요 없음
- SSH 포트만 열려있으면 됨 (보안상 권장)
- 개발용 컴퓨터에서 SSH 터널만 유지하면 됨 (별도 서비스 실행 불필요)

```bash
# 로컬 터미널에서 실행
ssh -L 30080:localhost:30080 \
    -L 30081:localhost:30081 \
    -L 30082:localhost:30082 \
    ubuntu@server-ip

# SSH 포트가 다른 경우
ssh -p 2222 -L 30080:localhost:30080 \
    -L 30081:localhost:30081 \
    -L 30082:localhost:30082 \
    ubuntu@server-ip

# 이제 로컬 브라우저에서 접속 (터널이 유지되는 동안)
# http://localhost:30080
# http://localhost:30081
# ws://localhost:30082
```

> 💡 **SSH 터널 동작 방식**:  
> 맥의 `localhost:30080`으로 들어오는 연결이 SSH 터널을 통해 서버의 `localhost:30080`으로 전달됩니다.  
> 따라서 서버에서 30080, 30081, 30082 포트를 외부에 개방할 필요가 없습니다.

### 방법 2: 직접 접속 (방화벽 오픈 필요)

**주의:** 보안상 권장하지 않습니다. SSH 터널링을 사용하는 것이 더 안전합니다.

```bash
# 서버에서 방화벽 설정
sudo ufw allow 30080/tcp
sudo ufw allow 30081/tcp
sudo ufw allow 30082/tcp

# 브라우저에서 직접 접속
# http://server-ip:30080
# http://server-ip:30081
# ws://server-ip:30082
```

---

## 🔄 개발 워크플로우

### 일일 개발 흐름

```bash
# 1. 로컬에서 코드 개발
vim control-pool/api-gateway.py

# 2. 로컬에서 유닛테스트 (선택)
python -m pytest tests/
# 또는 직접 실행
python control-pool/api-gateway.py

# 3. Git 커밋 (선택)
git add .
git commit -m "Update API Gateway"

# 4. 서버에 배포
./scripts/deploy-to-remote.sh -h server-ip

# 5. 로컬에서 로그 모니터링 (kubectl 설정 후)
kubectl logs -n control-pool -l app=api-gateway -f

# 6. 브라우저로 테스트 (SSH 터널 사용)
# 별도 터미널에서 SSH 터널 생성:
# ssh -L 30080:localhost:30080 -L 30081:localhost:30081 -L 30082:localhost:30082 ubuntu@server-ip
# 그 다음 브라우저에서 http://localhost:30080 접속
```

### 특정 서비스만 재배포

```bash
# 코드만 변경했을 때
./scripts/deploy-to-remote.sh -h server-ip

# 특정 서비스만 재시작 (kubectl 설정 후)
kubectl rollout restart deployment/api-gateway -n control-pool
kubectl rollout restart deployment/system-core -n calc-pool
```

---

## 🔒 보안 설정

### SSH Key 기반 인증 (비밀번호 입력 생략) ⭐ 필수 권장

**문제**: 배포 스크립트 실행 시 SSH 비밀번호를 여러 번 입력해야 함

**해결**: SSH 키 기반 인증 설정

#### 호스트에서 SSH 키 생성 및 복사

```bash
# 호스트(Mac/Windows)에서 실행 (컨테이너가 아닌 실제 컴퓨터)
ssh-keygen -t ed25519 -C "your-email@example.com"
# 키 파일 위치: ~/.ssh/id_ed25519 (또는 ~/.ssh/id_rsa)

# 기본 SSH 포트 (22)
ssh-copy-id ubuntu@server-ip

# 다른 SSH 포트 사용 시
ssh-copy-id -p 2222 ubuntu@server-ip
```

#### DevContainer 사용 시 주의사항

**⚠️ 중요**: DevContainer 내에서 SSH 키를 생성하면 안 됩니다!

- 컨테이너가 재생성될 때마다 새로운 키가 생성되어 서버에 키가 계속 쌓입니다
- 대신 **호스트의 SSH 키를 컨테이너에 마운트**하여 사용합니다

**DevContainer 설정**:

- `.devcontainer/devcontainer.json`에 호스트 SSH 키 마운트 설정이 포함되어 있습니다
- 컨테이너 재생성 시에도 호스트의 동일한 SSH 키를 사용합니다
- **Windows 사용자**: `devcontainer.json`의 mounts 경로를 `C:\Users\YourUsername\.ssh`로 수정하거나, `${localEnv:USERPROFILE}/.ssh`로 변경하세요

**설정 확인**:

```bash
# DevContainer 내에서 확인
ls -la ~/.ssh/
# 호스트의 SSH 키가 마운트되어 있어야 함

# SSH 키가 없으면 호스트에서 생성
# 호스트(Mac/Windows) 터미널에서:
ssh-keygen -t ed25519 -C "your-email@example.com"
ssh-copy-id -p 8027 user@server-ip
```

**설정 후**: 배포 스크립트 실행 시 비밀번호 입력 없이 자동 진행됩니다.

### 방화벽 설정 (서버)

**SSH 터널링 사용 시 (권장):**

```bash
# 서버에서 실행
sudo ufw allow 22/tcp      # SSH (또는 사용자 지정 포트)
sudo ufw allow 6443/tcp    # K3s API (kubectl 원격 제어 시)
sudo ufw enable

# 30080, 30081, 30082 포트는 개방할 필요 없음
# SSH 터널링을 통해 접속하므로 보안상 더 안전
```

**직접 접속 사용 시 (비권장):**

```bash
# 서버에서 실행
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 6443/tcp    # K3s API (kubectl 사용 시)
sudo ufw allow 30080/tcp   # API Gateway
sudo ufw allow 30081/tcp   # Monitor HTTP
sudo ufw allow 30082/tcp   # Monitor WebSocket
sudo ufw enable
```

### kubeconfig 보안

```bash
# 로컬에서 kubeconfig 권한 설정
chmod 600 ~/.kube/config
```

### sudo 비밀번호 없이 실행하기 (원격 배포 시) ⭐ 필수

**문제**: 원격 배포 시 다음 명령들이 sudo를 요구하지만, 비대화형 모드에서는 비밀번호를 입력할 수 없음:

- k3s 설치: `curl -sfL https://get.k3s.io | sh -` (내부적으로 sudo 사용)
- 이미지 import: `sudo k3s ctr images import`
- systemctl: `sudo systemctl enable k3s`

**해결**: sudo NOPASSWD 설정 (필수)

서버에서 실행:

```bash
# 서버에 SSH 접속
ssh -p 8027 user@server-ip

# sudoers 파일 편집
sudo visudo

# 다음 줄 추가 (user를 실제 사용자명으로 변경, 예: ubuntu, myuser 등)
user ALL=(ALL) NOPASSWD: ALL

# 또는 더 제한적으로 (보안상 권장)
user ALL=(ALL) NOPASSWD: /usr/local/bin/k3s, /usr/bin/systemctl, /usr/local/bin/k3s-uninstall.sh, /usr/bin/k3s
```

**설정 확인**:

```bash
# 서버에서 테스트
sudo -n true
# 출력이 없으면 성공 (비밀번호 없이 sudo 가능)
```

**참고**:

- `build-images.sh` 스크립트는 먼저 sudo 없이 시도하고, 실패하면 sudo를 사용합니다
- `install-k3s.sh` 스크립트는 비대화형 모드에서 sudo 권한을 자동으로 확인합니다
- sudo NOPASSWD가 설정되어 있지 않으면 배포가 실패합니다

---

## 🐛 문제 해결

### 서버에 접속할 수 없음

```bash
# 연결 테스트
ping server-ip
ssh -v ubuntu@server-ip

# 다른 SSH 포트 사용 시
ssh -v -p 2222 ubuntu@server-ip

# DNS가 안되면 /etc/hosts에 추가
echo "server-ip my-server" | sudo tee -a /etc/hosts
```

### 포트에 접속할 수 없음

```bash
# 서버에서 포트 확인
sudo netstat -tlnp | grep :30080

# K3s 상태 확인
sudo systemctl status k3s
```

### kubectl이 서버에 연결되지 않음

```bash
# kubeconfig 확인
cat ~/.kube/config | grep server

# 올바른 서버 주소인지 확인
# 127.0.0.1이 아닌 실제 서버 IP여야 함
```

### 이미지를 찾을 수 없음

```bash
# 서버에서 이미지 확인
sudo k3s ctr images list | grep pool

# 이미지가 없으면 다시 빌드
./scripts/build-images.sh
```

---

## 📊 유용한 명령어

### 상태 확인

```bash
# 모든 Pod 확인
kubectl get pods -A

# 특정 네임스페이스
kubectl get pods -n control-pool
kubectl get pods -n calc-pool

# 서비스 확인
kubectl get svc -A
```

### 로그 확인

```bash
# API Gateway 로그
kubectl logs -n control-pool -l app=api-gateway -f

# Monitor Service 로그
kubectl logs -n monitor-pool -l app=monitor-service -f

# Worker 로그
kubectl logs -n calc-pool -l app=system-core -f

# 최근 100줄만 보기
kubectl logs -n control-pool -l app=api-gateway --tail=100
```

### 재시작

```bash
# 특정 Deployment 재시작
kubectl rollout restart deployment/api-gateway -n control-pool
kubectl rollout restart deployment/system-core -n calc-pool

# 전체 재시작
kubectl rollout restart deployment -n control-pool
```

### 디버깅

```bash
# Pod 상세 정보
kubectl describe pod <pod-name> -n <namespace>

# 이벤트 확인
kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp

# Pod 내부 접속
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh
```

---

## 🚀 향후 계획: GitHub Actions 자동 배포

현재는 수동 배포이지만, 향후 GitHub Actions를 통한 자동 배포를 계획하고 있습니다.

### 예상 구조

```text
GitHub Push → GitHub Actions → 
  1. 코드 검증 (테스트)
  2. Docker 이미지 빌드
  3. 서버로 배포 (deploy-to-remote.sh 사용)
```

### 현재 코드 구조

- ✅ `scripts/deploy-to-remote.sh`: 배포 스크립트 (GitHub Actions에서도 사용 가능)
- ✅ `scripts/setup-remote-kubectl.sh`: kubectl 설정 (CI/CD에서도 사용 가능)
- ✅ 모든 스크립트는 독립적으로 실행 가능 (GitHub Actions에서 호출 가능)

### 향후 추가 예정

- `.github/workflows/deploy.yml`: GitHub Actions 워크플로우
- Secrets 설정: `REMOTE_HOST`, `REMOTE_USER`, `REMOTE_PORT`, SSH 키 등

---

## 💡 팁

### 빠른 재배포

```bash
# 코드만 변경했을 때
./scripts/deploy-to-remote.sh -h server-ip

# 코드 변경 후 캐시 없이 확실히 재빌드
./scripts/deploy-to-remote.sh -h server-ip --no-cache control-pool

# 설정(YAML)만 변경했을 때
./scripts/deploy-to-remote.sh -h server-ip --sync-only
ssh ubuntu@server-ip 'cd wireless-simulation-pipeline && kubectl apply -f control-pool/deployment.yaml'
```

### Git 기반 워크플로우

```bash
# 로컬에서 개발 후 Git push
git add .
git commit -m "Update API Gateway"
git push origin main

# 서버에서 pull 후 배포
ssh ubuntu@server-ip
cd /home/ubuntu/wireless-simulation-pipeline
git pull
./scripts/build-images.sh
kubectl rollout restart deployment/api-gateway -n control-pool
```

### 리소스 모니터링

```bash
# 서버 리소스 확인
kubectl top nodes
kubectl top pods -A

# GPU 사용량 확인 (nvidia-smi가 설치된 경우)
ssh ubuntu@server-ip 'nvidia-smi'
```

---

## 📚 다음 단계

1. ✅ **로컬 개발**: 코드 작성 및 유닛테스트
2. ✅ **서버 배포**: `deploy-to-remote.sh` 사용
3. ✅ **실제 테스트**: 서버에서 통합 테스트
4. 🔜 **자동 배포**: GitHub Actions 구축 (향후)

---

**원격 배포에 성공하셨나요?** 🚀 이제 로컬에서 개발하고 서버에서 실제 테스트할 수 있습니다!
