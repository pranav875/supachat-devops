#!/bin/bash

# Script to verify GitHub secrets are configured
# This doesn't actually check GitHub (requires API token), but helps you verify locally

echo "🔍 GitHub Secrets Verification Checklist"
echo "=========================================="
echo ""
echo "Please verify you have added these secrets to:"
echo "https://github.com/pranav875/supachat-devops/settings/secrets/actions"
echo ""

REQUIRED_SECRETS=(
    "GHCR_TOKEN"
    "SUPABASE_URL"
    "SUPABASE_SERVICE_KEY"
    "GROQ_API_KEY"
)

OPTIONAL_SECRETS=(
    "EC2_HOST"
    "EC2_SSH_KEY"
)

echo "✅ Required Secrets:"
for secret in "${REQUIRED_SECRETS[@]}"; do
    echo "   [ ] $secret"
done

echo ""
echo "⚠️  Optional Secrets (for EC2 deployment):"
for secret in "${OPTIONAL_SECRETS[@]}"; do
    echo "   [ ] $secret"
done

echo ""
echo "📋 Local .env file check:"
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
    
    # Check for required variables
    if grep -q "SUPABASE_URL=" .env; then
        echo "   ✅ SUPABASE_URL found"
    else
        echo "   ❌ SUPABASE_URL missing"
    fi
    
    if grep -q "SUPABASE_SERVICE_KEY=" .env; then
        echo "   ✅ SUPABASE_SERVICE_KEY found"
    else
        echo "   ❌ SUPABASE_SERVICE_KEY missing"
    fi
    
    if grep -q "GROQ_API_KEY=" .env; then
        echo "   ✅ GROQ_API_KEY found"
    else
        echo "   ❌ GROQ_API_KEY missing"
    fi
else
    echo "   ❌ .env file not found"
fi

echo ""
echo "🔐 To create GitHub Personal Access Token (GHCR_TOKEN):"
echo "   1. Visit: https://github.com/settings/tokens"
echo "   2. Click 'Generate new token (classic)'"
echo "   3. Select scope: write:packages"
echo "   4. Copy the token and add it as GHCR_TOKEN secret"
echo ""
echo "📝 To add secrets to GitHub:"
echo "   1. Go to: https://github.com/pranav875/supachat-devops/settings/secrets/actions"
echo "   2. Click 'New repository secret'"
echo "   3. Add each secret from the list above"
echo ""
echo "🚀 After adding secrets, enable the jobs in .github/workflows/deploy.yml"
echo "   Change 'if: false' to 'if: true' for build-push and deploy jobs"
echo ""
