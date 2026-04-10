# Deployment Guide

## Automated CI/CD Pipeline

Every push to `main` automatically:
1. ✅ Runs all tests (backend + frontend)
2. ✅ Builds Docker images
3. ✅ Pushes images to GitHub Container Registry

## Manual Deployment to EC2

After the CI/CD pipeline completes successfully, deploy to EC2:

### Quick Deploy

Connect to your EC2 instance and run:

```bash
cd ~/supachat
echo "YOUR_GITHUB_TOKEN" | sudo docker login ghcr.io -u pranav875 --password-stdin
sudo docker-compose pull
sudo docker-compose up -d
sudo docker-compose ps
```

### One-Line Deploy

Or use this single command:

```bash
cd ~/supachat && echo "YOUR_GITHUB_TOKEN" | sudo docker login ghcr.io -u pranav875 --password-stdin && sudo docker-compose pull && sudo docker-compose up -d && sudo docker-compose ps
```

Replace `YOUR_GITHUB_TOKEN` with your actual GitHub Personal Access Token.

## Verify Deployment

Check that containers are running:

```bash
sudo docker-compose ps
```

View logs:

```bash
sudo docker-compose logs --tail=50
```

Access your application:
```
http://YOUR_EC2_IP
```

## Cost Management

**Stop EC2 when not in use:**
- Go to AWS Console → EC2 → Instances
- Select instance → Instance state → Stop
- Cost when stopped: ~$1-2/month (storage only)

**Start EC2 when needed:**
- Select instance → Instance state → Start
- Wait 1-2 minutes for it to boot
- Deploy latest images using commands above

## Summary

Your DevOps setup includes:
- ✅ Complete CI/CD pipeline (test + build + push)
- ✅ Docker containerization
- ✅ GitHub Container Registry
- ✅ AWS EC2 hosting
- ✅ Monitoring stack (Grafana, Prometheus, Loki)
- ⚡ One-command manual deployment

This is a production-ready DevOps workflow!
