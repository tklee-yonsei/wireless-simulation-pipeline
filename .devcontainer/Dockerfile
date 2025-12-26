# Python 개발용 devcontainer
FROM python:3.11-slim

# 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 비-root 사용자 생성
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && rm -rf /var/lib/apt/lists/*

# Python 개발 도구 설치
RUN pip install --no-cache-dir \
    # 프로젝트 의존성
    flask \
    flask-socketio \
    flask-cors \
    redis \
    requests \
    python-socketio[client] \
    websocket-client \
    numpy \
    # 개발/테스트 도구
    pytest \
    pytest-cov \
    ruff \
    black \
    pylint \
    httpx

# 작업 디렉토리 설정
WORKDIR /workspaces

USER $USERNAME
