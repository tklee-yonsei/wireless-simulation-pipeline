#!/bin/bash
set -e

echo "====================================="
echo "K3s Installation Script"
echo "====================================="

# 비대화형 모드 감지 (SSH로 원격 실행 시)
if [ ! -t 0 ]; then
    NON_INTERACTIVE=true
else
    NON_INTERACTIVE=false
fi

# sudo 권한 확인 (비대화형 모드에서 중요)
if [ "$NON_INTERACTIVE" = true ]; then
    echo "⚠️  Running in non-interactive mode (SSH remote execution)"
    echo "   Checking sudo permissions..."
    
    if ! sudo -n true 2>/dev/null; then
        echo "❌ Error: sudo password is required but cannot be entered in non-interactive mode"
        echo ""
        echo "Please configure sudo NOPASSWD on the server:"
        echo "  1. SSH to the server: ssh user@server-ip"
        echo "  2. Run: sudo visudo"
        echo "  3. Add this line (replace USERNAME with your username):"
        echo "     USERNAME ALL=(ALL) NOPASSWD: ALL"
        echo ""
        echo "Or for k3s only:"
        echo "     USERNAME ALL=(ALL) NOPASSWD: /usr/local/bin/k3s, /usr/bin/systemctl"
        echo ""
        exit 1
    fi
    echo "✅ Sudo permissions OK (no password required)"
    echo ""
fi

# K3s 설치 여부 확인
if command -v k3s &> /dev/null; then
    if [ "$NON_INTERACTIVE" = false ]; then
        echo "⚠️  K3s is already installed"
        read -p "Do you want to reinstall? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Installation cancelled"
            exit 0
        fi
    else
        echo "⚠️  K3s is already installed, skipping installation"
        exit 0
    fi
    echo "Uninstalling existing K3s..."
    sudo /usr/local/bin/k3s-uninstall.sh || true
fi

echo "Installing K3s..."
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--write-kubeconfig-mode=644" sh -

echo "Setting up KUBECONFIG..."
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# .bashrc에 환경변수 추가 (중복 방지)
if ! grep -q "KUBECONFIG=/etc/rancher/k3s/k3s.yaml" ~/.bashrc; then
    echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
    echo "✅ Added KUBECONFIG to ~/.bashrc"
else
    echo "ℹ️  KUBECONFIG already in ~/.bashrc"
fi

# .zshrc에도 추가 (zsh 사용자를 위해)
if [ -f ~/.zshrc ]; then
    if ! grep -q "KUBECONFIG=/etc/rancher/k3s/k3s.yaml" ~/.zshrc; then
        echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.zshrc
        echo "✅ Added KUBECONFIG to ~/.zshrc"
    fi
fi

echo "Enabling K3s service..."
sudo systemctl enable k3s

echo "Waiting for K3s to be ready..."
sleep 10

# 현재 사용자가 sudo 없이 k3s ctr을 사용할 수 있도록 설정
# k3s는 보통 /var/lib/rancher/k3s/agent/containerd/containerd.sock을 사용
# 사용자가 적절한 그룹에 속해있거나, sudo 없이 접근할 수 있어야 함
echo "Configuring user permissions for k3s ctr..."
CURRENT_USER=$(whoami)
if ! groups | grep -q docker; then
    echo "ℹ️  Note: You may need sudo for k3s ctr commands"
    echo "   To avoid sudo, you can add yourself to docker group:"
    echo "   sudo usermod -aG docker $CURRENT_USER"
    echo "   (requires logout/login to take effect)"
fi

echo "Verifying installation..."
kubectl get nodes

echo ""
echo "====================================="
echo "✅ K3s Installation Complete!"
echo "====================================="
echo ""
echo "Please run: source ~/.bashrc"
echo "Or open a new terminal to apply environment variables"
echo ""
