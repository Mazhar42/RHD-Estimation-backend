#!/bin/bash
# Remote Deployment Script
# Run this script on your server via SSH from GitHub Actions
# Usage: bash deploy-remote.sh

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/rhd-estimation"
BACKEND_DIR="$PROJECT_DIR/backend"
LOG_FILE="$PROJECT_DIR/deployment.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Ensure we have proper permissions
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}✗ This script must be run as root${NC}"
   exit 1
fi

# Logging function
log() {
    echo -e "${TIMESTAMP} - $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "${RED}✗ Error: $1${NC}"
    exit 1
}

success() {
    log "${GREEN}✓ $1${NC}"
}

# Change to backend directory
cd "$BACKEND_DIR" || error_exit "Backend directory not found at $BACKEND_DIR"

log "${BLUE}========================================${NC}"
log "${BLUE}Starting Remote Deployment${NC}"
log "${BLUE}========================================${NC}"

# Step 1: Pull latest changes
log "${YELLOW}[1/7] Pulling latest changes from GitHub...${NC}"
git fetch origin || error_exit "Failed to fetch from origin"
git reset --hard origin/main || error_exit "Failed to reset to origin/main"
success "Code updated"

# Step 2: Check environment
log "${YELLOW}[2/7] Verifying environment configuration...${NC}"
if [ ! -f "$BACKEND_DIR/.env.prod" ]; then
    error_exit ".env.prod not found. Please create it first."
fi
success "Environment configuration found"

# Step 3: Build Docker image
log "${YELLOW}[3/7] Building Docker image...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache 2>&1 | tee -a "$LOG_FILE" || error_exit "Docker build failed"
success "Docker image built"

# Step 4: Backup database (optional but recommended)
log "${YELLOW}[4/7] Backing up database...${NC}"
BACKUP_DIR="$PROJECT_DIR/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).sql"

if docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
    success "Database backed up to $BACKUP_FILE"
else
    log "${YELLOW}⚠ Database backup skipped (first deployment)${NC}"
fi

# Step 5: Stop old containers
log "${YELLOW}[5/7] Stopping old containers...${NC}"
docker-compose -f docker-compose.prod.yml down 2>&1 | tee -a "$LOG_FILE" || error_exit "Failed to stop containers"
success "Old containers stopped"

# Step 6: Start new containers
log "${YELLOW}[6/7] Starting new containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d 2>&1 | tee -a "$LOG_FILE" || error_exit "Failed to start containers"
success "New containers started"

# Step 7: Health check
log "${YELLOW}[7/7] Performing health checks...${NC}"

# Wait for database to be ready
log "Waiting for database to be ready..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U "$DB_USER" > /dev/null 2>&1; then
        success "Database is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        error_exit "Database failed to start after 30 seconds"
    fi
    echo -n "."
    sleep 1
done

# Wait for backend to be ready
log "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        success "Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        error_exit "Backend failed to start after 30 seconds"
    fi
    echo -n "."
    sleep 1
done

# Final status check
log "${BLUE}========================================${NC}"
log "${BLUE}Checking Final Status${NC}"
log "${BLUE}========================================${NC}"

docker-compose -f docker-compose.prod.yml ps

echo ""
log "${GREEN}========================================${NC}"
log "${GREEN}✓ Deployment Completed Successfully!${NC}"
log "${GREEN}========================================${NC}"
log "API Health: $(curl -s http://localhost:8000/health | python3 -m json.tool)"
log "Deployment Log: $LOG_FILE"
