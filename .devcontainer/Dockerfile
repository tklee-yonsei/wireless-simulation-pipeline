# Python 개발용 devcontainer
FROM python:3.11-slim

# 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    git \
    vim \
    rsync \
    openssh-client \
    ca-certificates \
    bash \
    bash-completion \
    && rm -rf /var/lib/apt/lists/*

# kubectl 설치
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/kubectl \
    && kubectl version --client

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

# bash를 기본 쉘로 설정 및 터미널 설정
RUN chsh -s /bin/bash $USERNAME || true && \
    echo 'export TERM=xterm-256color' >> /home/$USERNAME/.bashrc && \
    chown $USERNAME:$USERNAME /home/$USERNAME/.bashrc

# .inputrc 파일 생성 (readline 설정 - 화살표 키 등)
RUN echo 'set editing-mode emacs' > /home/$USERNAME/.inputrc && \
    echo 'set completion-ignore-case on' >> /home/$USERNAME/.inputrc && \
    echo 'set show-all-if-ambiguous on' >> /home/$USERNAME/.inputrc && \
    chown $USERNAME:$USERNAME /home/$USERNAME/.inputrc

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
