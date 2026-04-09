# GitHub Secrets Setup Guide

This guide will help you configure the required secrets for your CI/CD pipeline.

## Step 1: Create GitHub Personal Access Token (GHCR_TOKEN)

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: `SupaChat GHCR Token`
4. Set expiration: Choose your preference (recommend 90 days or No expiration for learning)
5. Select scopes:
   - ✅ `write:packages` (includes read:packages)
   - ✅ `delete:packages` (optional, for cleanup)
6. Click "Generate token"
7. **COPY THE TOKEN** - you won't see it again!

## Step 2: Add Secrets to GitHub Repository

1. Go to your repository: https://github.com/pranav875/supachat-devops
2. Click "Settings" tab
3. In the left sidebar, click "Secrets and variables" → "Actions"
4. Click "New repository secret" for each of the following:

### Required Secrets:

#### 1. GHCR_TOKEN
- **Value**: Paste the Personal Access Token from Step 1
- **Purpose**: Allows GitHub Actions to push Docker images to GitHub Container Registry

#### 2. SUPABASE_URL
- **Value**: `https://mmrrxoxaqrfkffffblvc.supabase.co`
- **Purpose**: Your Supabase project URL
- **Note**: Get this from your .env file

#### 3. SUPABASE_SERVICE_KEY
- **Value**: Get from your `.env` file (starts with `eyJhbGciOiJIUzI1NiIs...`)
- **Purpose**: Service role key for Supabase backend access
- **Note**: This is a long JWT token

#### 4. GROQ_API_KEY
- **Value**: Get from your `.env` file (starts with `gsk_...`)
- **Purpose**: API key for Groq LLM service
- **Note**: Keep this secret and never commit to repository

#### 5. EC2_HOST (Optional - only if deploying to EC2)
- **Value**: Your EC2 instance public IP or hostname (e.g., `ec2-13-233-123-45.ap-south-1.compute.amazonaws.com`)
- **Purpose**: SSH connection to your EC2 instance

#### 6. EC2_SSH_KEY (Optional - only if deploying to EC2)
- **Value**: Your EC2 private key (entire content of your .pem file)
- **Purpose**: SSH authentication to EC2
- **Format**:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
...your key content...
-----END RSA PRIVATE KEY-----
```

## Step 3: Enable Build and Deploy Jobs

Once all secrets are added, update `.github/workflows/deploy.yml`:

1. Find the `build-push` job
2. Change `if: false` to `if: true` (or remove the line)
3. If you have EC2 configured, do the same for the `deploy` job
4. Commit and push the changes

## Step 4: Verify Setup

After pushing changes:
1. Go to "Actions" tab in your repository
2. Click on the latest workflow run
3. All jobs should show green checkmarks ✅

## Troubleshooting

### GHCR Login Failed
- Verify your Personal Access Token has `write:packages` scope
- Make sure the token hasn't expired
- Check that the secret name is exactly `GHCR_TOKEN`

### EC2 Connection Failed
- Verify EC2 instance is running
- Check security group allows SSH (port 22) from GitHub Actions IPs
- Ensure the SSH key format is correct (includes BEGIN/END lines)
- Verify the username is correct (usually `ec2-user` for Amazon Linux, `ubuntu` for Ubuntu)

### Docker Build Failed
- Check Dockerfile syntax
- Verify all required files are in the repository
- Check build logs for specific errors

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit secrets to your repository
- The `.env` file should be in `.gitignore`
- Rotate keys periodically
- Use least-privilege access (only grant necessary permissions)
- For production, consider using AWS Secrets Manager or similar

## Quick Setup Commands

After adding secrets to GitHub, run:

```bash
# Enable build and deploy jobs
git pull
# Edit .github/workflows/deploy.yml and change if: false to if: true
git add .github/workflows/deploy.yml
git commit -m "Enable build-push and deploy jobs"
git push
```

## Next Steps

1. ✅ Add all required secrets to GitHub
2. ✅ Enable build-push job
3. ✅ (Optional) Set up EC2 instance and enable deploy job
4. ✅ Push changes and verify pipeline runs successfully
5. ✅ Access your deployed application

---

Need help? Check the GitHub Actions logs for detailed error messages.
