# EC2 Setup Guide for SupaChat

This guide will help you set up an EC2 instance for deploying SupaChat with minimal cost.

## Prerequisites

- AWS Account (create at https://aws.amazon.com if you don't have one)
- Credit/Debit card for AWS verification (won't be charged if using free tier)

## Step 1: Launch EC2 Instance

### 1.1 Go to EC2 Console
1. Log in to AWS Console: https://console.aws.amazon.com
2. Search for "EC2" in the top search bar
3. Click "Launch Instance"

### 1.2 Configure Instance

**Name and Tags:**
- Name: `supachat-server`

**Application and OS Images (AMI):**
- Select: **Amazon Linux 2023 AMI** (Free tier eligible)
- Architecture: 64-bit (x86)

**Instance Type:**
- Select: **t2.micro** (Free tier eligible: 1 vCPU, 1 GB RAM)
- Or **t3.micro** if t2.micro not available

**Key Pair (login):**
- Click "Create new key pair"
- Key pair name: `supachat-key`
- Key pair type: RSA
- Private key file format: `.pem`
- Click "Create key pair" - **SAVE THIS FILE SECURELY!**

**Network Settings:**
- Click "Edit"
- Auto-assign public IP: **Enable**
- Firewall (security groups): Create new security group
  - Security group name: `supachat-sg`
  - Description: `Security group for SupaChat application`
  
**Add these Security Group Rules:**

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web access |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web access |
| Custom TCP | TCP | 3000 | 0.0.0.0/0 | Frontend (optional) |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | Backend API (optional) |

**Configure Storage:**
- Size: **20 GB** (Free tier includes 30 GB)
- Volume type: gp3 (General Purpose SSD)

**Advanced Details:**
- Leave as default

### 1.3 Launch Instance
- Click "Launch instance"
- Wait for instance state to be "Running" (takes 1-2 minutes)

## Step 2: Connect to Your EC2 Instance

### 2.1 Get Instance Details
1. Go to EC2 Dashboard → Instances
2. Select your instance
3. Note down:
   - **Public IPv4 address** (e.g., 13.233.123.45)
   - **Public IPv4 DNS** (e.g., ec2-13-233-123-45.ap-south-1.compute.amazonaws.com)

### 2.2 Set Key Permissions (On Your Local Machine)

```bash
# Move the key to a safe location
mkdir -p ~/.ssh
mv ~/Downloads/supachat-key.pem ~/.ssh/
chmod 400 ~/.ssh/supachat-key.pem
```

### 2.3 Connect via SSH

```bash
# Replace with your instance's public IP
ssh -i ~/.ssh/supachat-key.pem ec2-user@YOUR_INSTANCE_IP
```

Example:
```bash
ssh -i ~/.ssh/supachat-key.pem ec2-user@13.233.123.45
```

## Step 3: Set Up EC2 Instance

Once connected to your EC2 instance, run these commands:

```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

# Log out and log back in for docker group to take effect
exit
```

### Reconnect:
```bash
ssh -i ~/.ssh/supachat-key.pem ec2-user@YOUR_INSTANCE_IP
```

## Step 4: Set Up Application Directory

```bash
# Create application directory
mkdir -p ~/supachat
cd ~/supachat

# Create .env file
cat > .env << 'EOF'
# Supabase
SUPABASE_URL=https://mmrrxoxaqrfkffffblvc.supabase.co
SUPABASE_SERVICE_KEY=YOUR_SUPABASE_SERVICE_KEY_HERE
DATABASE_URL=YOUR_DATABASE_URL_HERE

# LLM
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE

# App
HISTORY_LIMIT=50
HISTORY_DB_PATH=/app/data/supachat_history.db
NEXT_PUBLIC_API_URL=http://YOUR_INSTANCE_IP/api
EOF

# Edit the .env file with your actual values
nano .env
```

**Replace these values in .env:**
- `YOUR_SUPABASE_SERVICE_KEY_HERE` - from your local .env
- `YOUR_DATABASE_URL_HERE` - from your local .env
- `YOUR_GROQ_API_KEY_HERE` - from your local .env
- `YOUR_INSTANCE_IP` - your EC2 public IP

Save and exit (Ctrl+X, then Y, then Enter)

## Step 5: Create docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
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
      - NEXT_PUBLIC_API_URL=http://YOUR_INSTANCE_IP/api
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

# Replace YOUR_INSTANCE_IP with your actual IP
sed -i "s/YOUR_INSTANCE_IP/$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)/g" docker-compose.yml
```

## Step 6: Log in to GitHub Container Registry

```bash
# Create a GitHub Personal Access Token if you haven't already
# Then log in to GHCR
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

Replace:
- `YOUR_GITHUB_TOKEN` - Your GitHub Personal Access Token (same as GHCR_TOKEN)
- `YOUR_GITHUB_USERNAME` - Your GitHub username (pranav875)

## Step 7: Deploy Application

```bash
# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Step 8: Add EC2 Secrets to GitHub

Now add these secrets to your GitHub repository:

1. Go to: https://github.com/pranav875/supachat-devops/settings/secrets/actions
2. Add these secrets:

**EC2_HOST:**
```
YOUR_INSTANCE_PUBLIC_IP
```

**EC2_SSH_KEY:**
```
-----BEGIN RSA PRIVATE KEY-----
[Paste entire content of supachat-key.pem file]
-----END RSA PRIVATE KEY-----
```

To get the key content:
```bash
cat ~/.ssh/supachat-key.pem
```

## Step 9: Enable Deploy Job

After adding secrets, enable the deploy job in your workflow.

## Step 10: Access Your Application

Open in browser:
```
http://YOUR_INSTANCE_IP
```

## Cost Management

### Stop Instance When Not in Use:
```bash
# From AWS Console:
# EC2 → Instances → Select instance → Instance state → Stop
```

**Cost when stopped:** ~$1-2/month (only storage)
**Cost when running:** ~$8-10/month (if not on free tier)

### Set Up Billing Alert:
1. Go to AWS Billing Dashboard
2. Click "Budgets"
3. Create budget: $5/month alert

### Terminate Instance (Delete Everything):
```bash
# WARNING: This deletes everything!
# EC2 → Instances → Select instance → Instance state → Terminate
```

## Troubleshooting

### Can't connect via SSH:
- Check security group allows SSH from your IP
- Verify key permissions: `chmod 400 ~/.ssh/supachat-key.pem`
- Use correct username: `ec2-user` for Amazon Linux

### Docker permission denied:
- Log out and log back in after adding user to docker group
- Or use: `sudo docker` commands

### Application not accessible:
- Check security group allows HTTP (port 80)
- Verify containers are running: `docker-compose ps`
- Check logs: `docker-compose logs`

### Out of memory:
- t2.micro has only 1GB RAM
- Consider upgrading to t3.small (costs more)
- Or optimize your application

## Useful Commands

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update to latest images
docker-compose pull
docker-compose up -d

# Check disk space
df -h

# Check memory usage
free -h

# Monitor resources
htop  # (install with: sudo yum install -y htop)
```

## Next Steps

1. ✅ Set up custom domain (optional)
2. ✅ Configure SSL/HTTPS with Let's Encrypt (optional)
3. ✅ Set up monitoring with CloudWatch (optional)
4. ✅ Configure automatic backups (optional)

---

**Remember:** Stop your EC2 instance when not actively using it to minimize costs!
