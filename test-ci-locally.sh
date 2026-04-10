#!/bin/bash
set -e

echo "=== Testing CI Pipeline Locally ==="

echo "Step 1: Backend Tests"
cd backend
export DATABASE_URL="postgresql://testuser:testpass@localhost:5432/testdb"
export TEST_DATABASE_URL="postgresql://testuser:testpass@localhost:5432/testdb"
export GROQ_API_KEY="test-key"
export SUPABASE_URL="http://test-supabase-url.com"
export SUPABASE_SERVICE_KEY="test-key"

echo "Installing backend dependencies..."
pip install -q -r requirements.txt

echo "Running backend tests..."
pytest --tb=short -v

cd ..

echo ""
echo "Step 2: Frontend Tests"
cd frontend

echo "Installing frontend dependencies..."
npm ci --silent

echo "Cleaning build artifacts..."
rm -rf .next .swc

echo "Running frontend tests..."
npm test

cd ..

echo ""
echo "=== All Tests Passed! ==="
