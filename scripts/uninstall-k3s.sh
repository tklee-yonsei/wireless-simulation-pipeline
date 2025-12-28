#!/bin/bash
set -e

echo "====================================="
echo "K3s Uninstallation Script"
echo "====================================="

echo ""
echo "⚠️  WARNING: This will completely remove K3s and all data"
echo "⚠️  All Kubernetes resources will be deleted"
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled"
    exit 0
fi

# K3s 설치 여부 확인
if ! command -v k3s &> /dev/null; then
    echo "ℹ️  K3s is not installed"
    exit 0
fi

echo ""
echo "🗑️  Uninstalling K3s..."
sudo /usr/local/bin/k3s-uninstall.sh

echo ""
echo "🧹 Cleaning up environment variables..."

# .bashrc에서 KUBECONFIG 제거
if [ -f ~/.bashrc ]; then
    sed -i '/KUBECONFIG=\/etc\/rancher\/k3s\/k3s.yaml/d' ~/.bashrc
    echo "✅ Removed KUBECONFIG from ~/.bashrc"
fi

# .zshrc에서 KUBECONFIG 제거
if [ -f ~/.zshrc ]; then
    sed -i '/KUBECONFIG=\/etc\/rancher\/k3s\/k3s.yaml/d' ~/.zshrc
    echo "✅ Removed KUBECONFIG from ~/.zshrc"
fi

echo ""
echo "====================================="
echo "✅ K3s Uninstallation Complete!"
echo "====================================="
echo ""
echo "Please run: source ~/.bashrc"
echo "Or open a new terminal"
echo ""
