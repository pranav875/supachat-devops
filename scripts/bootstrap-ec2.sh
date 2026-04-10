#!/bin/bash
# bootstrap-ec2.sh — Run this ONCE on a fresh Amazon Linux 2023 EC2 instance
# Usage: bash bootstrap-ec2.sh
set -euo pipefail

echo "==> Updating system packages..."
sudo dnf update -y

echo "==> Installing Docker..."
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

echo "==> Installing Docker Compose plugin..."
COMPOSE_VERSION=$(curl -fsSL https://api.github.com/repos/docker/compose/releases/latest \
  | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -fsSL \
  "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

echo "==> Verifying installations..."
docker --version
docker compose version

echo "==> Creating app directory..."
mkdir -p ~/supachat

echo ""
echo "Bootstrap complete!"
echo ""
echo "IMPORTANT: Log out and back in so docker group takes effect:"
echo "  exit"
echo "  ssh -i your-key.pem ec2-user@YOUR_IP"
echo ""
echo "Then create ~/supachat/.env with your credentials:"
echo "  nano ~/supachat/.env"
echo ""
echo "Required .env keys:"
echo "  SUPABASE_URL="
echo "  SUPABASE_SERVICE_KEY="
echo "  DATABASE_URL="
echo "  GROQ_API_KEY="
echo "  NEXT_PUBLIC_API_URL=http://YOUR_EC2_IP/api"
