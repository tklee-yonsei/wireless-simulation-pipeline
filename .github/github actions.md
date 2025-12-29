# GitHub Actions (향후 계획)

이 디렉토리는 향후 GitHub Actions를 통한 자동 배포를 위해 준비된 공간입니다.

## 현재 상태

- ✅ **수동 배포**: `scripts/deploy-to-remote.sh` 사용
- 🔜 **자동 배포**: GitHub Actions 워크플로우 (향후 추가 예정)

## 향후 계획

### 예상 워크플로우

```yaml
# .github/workflows/deploy.yml (향후 추가 예정)
name: Deploy to Server

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to remote server
        run: ./scripts/deploy-to-remote.sh -h ${{ secrets.REMOTE_HOST }} --no-cache control-pool
        env:
          REMOTE_HOST: ${{ secrets.REMOTE_HOST }}
          REMOTE_USER: ${{ secrets.REMOTE_USER }}
          # 선택사항: 특정 풀만 캐시 없이 재빌드
          # --no-cache control-pool calc-pool
```

### 필요한 GitHub Secrets

- `REMOTE_HOST`: Ubuntu 서버 IP 또는 도메인
- `REMOTE_USER`: SSH 사용자명
- `SSH_PRIVATE_KEY`: 서버 접속용 SSH 개인키

## 현재 사용 방법

수동 배포를 사용하세요:

```bash
# 기본 배포
./scripts/deploy-to-remote.sh -h <server-ip>

# 특정 풀만 캐시 없이 재빌드
./scripts/deploy-to-remote.sh -h <server-ip> --no-cache control-pool calc-pool
```

자세한 내용은 [REMOTE-DEPLOYMENT.md](../REMOTE-DEPLOYMENT.md)를 참고하세요.

