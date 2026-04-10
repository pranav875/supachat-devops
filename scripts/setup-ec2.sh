#!/bin/bash

# EC2 Setup Script for SupaChat
# Run this script on your EC2 instance after connecting via SSH

set -e

echo "🚀 SupaChat EC2 Setup Script"
echo "=============================="
echo ""

# Check if running on EC2
if [ ! -f /sys/hypervisor/uuid ] || ! grep -q ec2 /sys/hypervisor/uuid 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be an EC2 instance"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
sudo yum update -y

echo ""
echo "Step 2: Installing Docker..."
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

echo ""
echo "Step 3: Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo ""
echo "Step 4: Installing useful tools..."
sudo yum install -y git htop curl wget

echo ""
echo "Step 5: Creating application directory..."
mkdir -p ~/supachat
cd ~/supachat

echo ""
echo "Step 6: Getting instance metadata..."
INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "Your instance IP: $INSTANCE_IP"

echo ""
echo "Step 7: Creating .env file..."
cat > .env << EOF
# Supabase
SUPABASE_URL=REPLACE_WITH_YOUR_SUPABASE_URL
SUPABASE_SERVICE_KEY=REPLACE_WITH_YOUR_SUPABASE_SERVICE_KEY
DATABASE_URL=REPLACE_WITH_YOUR_DATABASE_URL

# LLM
GROQ_API_KEY=REPLACE_WITH_YOUR_GROQ_API_KEY

# App
HISTORY_LIMIT=50
HISTORY_DB_PATH=/app/data/supachat_history.db
NEXT_PUBLIC_API_URL=http://${INSTANCE_IP}/api
EOF

echo ""
echo "Step 8: Creating docker-compose.yml..."
cat > docker-compose.yml << EOF
version: '3.8'

services:
  backend:
    image: ghcr.io/pranav875/supachat-backend:latest
    container_name: supachat-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: ghcr.io/pranav875/supachat-frontend:latest
    container_name: supachat-frontend
    restart: unless-stopped
    ports:
      - "80:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://${INSTANCE_IP}/api
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  data:
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your credentials:"
echo "   nano ~/supachat/.env"
echo ""
echo "2. Log in to GitHub Container Registry:"
echo "   echo 'YOUR_GITHUB_TOKEN' | docker login ghcr.io -u pranav875 --password-stdin"
echo ""
echo "3. Deploy the application:"
echo "   cd ~/supachat"
echo "   docker-compose pull"
echo "   docker-compose up -d"
echo ""
echo "4. Check status:"
echo "   docker-compose ps"
echo ""
echo "5. Access your app at:"
echo "   http://${INSTANCE_IP}"
echo ""
echo "⚠️  IMPORTANT: You need to log out and log back in for Docker permissions to take effect!"
echo ""
