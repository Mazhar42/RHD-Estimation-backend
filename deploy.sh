#!/bin/bash
# Production Deployment Script for RHD Estimation Backend
# Run this after configuring .env.prod

set -euo pipefail

echo "======================================"
echo "RHD Estimation Backend Deployment"
echo "======================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo -e "${RED}✗ Error: .env.prod not found${NC}"
    echo "Please create .env.prod from .env.prod.template first:"
    echo "  cp .env.prod.template .env.prod"
    exit 1
fi

# Load environment variables
export $(cat .env.prod | grep -v '^#' | xargs)

# Check if SECRET_KEY is set
if [ -z "${SECRET_KEY}" ] || [ "$SECRET_KEY" = "your-strong-secret-key-here" ]; then
    echo -e "${RED}✗ Error: SECRET_KEY is not properly configured${NC}"
    echo "Generate a new one with:"
    echo "  python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
    exit 1
fi

echo -e "${GREEN}✓ Configuration loaded${NC}"

# Step 1: Build the Docker image
echo ""
echo -e "${YELLOW}[1/5] Building Docker image...${NC}"
docker-compose -f docker-compose.prod.yml build
echo -e "${GREEN}✓ Docker image built${NC}"

# Step 2: Start services
echo ""
echo -e "${YELLOW}[2/5] Starting services...${NC}"
docker-compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}✓ Services started${NC}"

# Step 3: Wait for database to be ready
echo ""
echo -e "${YELLOW}[3/5] Waiting for database to be ready...${NC}"
sleep 10
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U "$DB_USER" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Database failed to start${NC}"
        exit 1
    fi
    echo "Waiting... ($i/30)"
    sleep 1
done

# Step 4: Check application health
echo ""
echo -e "${YELLOW}[4/5] Checking application health...${NC}"
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Application is healthy${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Application failed to start${NC}"
        docker-compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
    echo "Waiting for app... ($i/30)"
    sleep 1
done

# Step 5: View logs
echo ""
echo -e "${YELLOW}[5/5] Recent logs${NC}"
docker-compose -f docker-compose.prod.yml logs --tail=20 backend

echo ""
echo -e "${GREEN}======================================"
echo "✓ Deployment Complete!"
echo "=====================================${NC}"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Database: $DB_HOST:$DB_PORT"
echo ""
echo "View logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f backend"
echo ""
echo "Stop services:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
