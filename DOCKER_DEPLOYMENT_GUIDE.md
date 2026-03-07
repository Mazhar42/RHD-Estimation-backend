# Docker Deployment Guide for RHD Estimation Backend

## 📋 Project Audit Summary

### ✅ Strengths

1. **Password Hashing**: Using Argon2 (strong hashing algorithm)
2. **JWT Authentication**: Properly implemented with expiration
3. **Role-Based Access Control (RBAC)**: Comprehensive permission system
4. **CORS Configuration**: Properly restricted to known origins (not using "\*")
5. **Database Abstraction**: SQLAlchemy with proper session management
6. **SSL/TLS Support**: PostgreSQL connections use SSL in production
7. **Pydantic**: Using pydantic-settings for configuration management
8. **Logging**: Implemented across auth and critical sections

### ⚠️ Security Concerns & Issues

#### 🔴 Critical Issues

1. **Hardcoded Default SECRET_KEY in security.py**
   - Location: [app/security.py](app/security.py#L11)
   - Issue: `SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-environment")`
   - Risk: If SECRET_KEY env var not set, uses insecure default
   - Fix: Remove default, require env variable in production

2. **Production Database Credentials in .env.production**
   - Location: [.env.production](.env.production)
   - Risk: Database URL with hardcoded credentials committed to version control
   - Fix: Use environment variables from container orchestration (Docker secrets, Kubernetes, cloud provider)
   - Don't: Commit sensitive .env files to Git

3. **Missing HTTPS Enforcement**
   - No HTTP → HTTPS redirect
   - No secure headers middleware
   - Risk: Man-in-the-middle attacks, session hijacking

4. **No Rate Limiting**
   - Auth endpoints vulnerable to brute force attacks
   - No protection against credential stuffing
   - Risk: Account compromise

5. **Missing Request Validation Size Limits**
   - No max request body size set
   - Risk: Denial of Service (DoS) attacks

#### 🟡 Medium Issues

1. **Weak CORS Configuration for Development**
   - Allows all localhost ports: `http://localhost:\d+`
   - Dev origins hardcoded in code
   - Fix: Move to environment variables

2. **Missing Security Headers**
   - No X-Frame-Options
   - No X-Content-Type-Options
   - No Strict-Transport-Security
   - No Content-Security-Policy

3. **Database Column Name Potential Vulnerability**
   - Using `organization` as VARCHAR in items table
   - Could be subject to SQL injection if using raw SQL
   - Mitigation: Ensure all queries use parameterized queries (already done via SQLAlchemy)

4. **Logging May Expose Sensitive Data**
   - Check that JWT tokens are not logged
   - Currently appears safe but monitor

#### 🟢 Minor Issues

1. **Missing Environment Variable Documentation**
   - Create a `.env.example` template listing all required vars
   - Update: [.env.example](.env.example) has basic vars but missing SECRET_KEY, CORS_ORIGINS

2. **No Health Check Endpoint**
   - Needed for Docker container orchestration
   - Implement `/health` endpoint

---

## 🐳 Docker Setup

### Dockerfile

Create `Dockerfile` in the root directory:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Run with production-grade ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Docker Compose (Development)

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  db:
    image: postgres:16-alpine
    container_name: rhd-estimation-db
    environment:
      POSTGRES_USER: ${DB_USER:-estimation_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
      POSTGRES_DB: ${DB_NAME:-rhd_estimation}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-estimation_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: .
    container_name: rhd-estimation-backend
    environment:
      APP_ENV: development
      DATABASE_URL: postgresql://${DB_USER:-estimation_user}:${DB_PASSWORD:-changeme}@db:5432/${DB_NAME:-rhd_estimation}
      SECRET_KEY: ${SECRET_KEY:-your-dev-secret-key-change-in-production}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    networks:
      - app-network

  # Optional: pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@example.com}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
    ports:
      - "5050:80"
    depends_on:
      - db
    networks:
      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

### Docker Compose (Production)

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
  db:
    image: postgres:16-alpine
    container_name: rhd-estimation-db-prod
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: .
    container_name: rhd-estimation-backend-prod
    restart: always
    environment:
      APP_ENV: production
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network

volumes:
  postgres_data_prod:

networks:
  app-network:
    driver: bridge
```

### Environment Variables (.env template for production)

Create `.env.prod.template`:

```env
# Production Environment Variables (Copy to .env and fill in)

# App Configuration
APP_ENV=production
SECRET_KEY=<GENERATE_A_STRONG_KEY_HERE>

# Database (Must use strong passwords in production)
DB_USER=rhd_estimation_user
DB_PASSWORD=<STRONG_PASSWORD_HERE>
DB_HOST=db
DB_PORT=5432
DB_NAME=rhd_estimation
DATABASE_URL=postgresql://rhd_estimation_user:<STRONG_PASSWORD_HERE>@db:5432/rhd_estimation

# CORS Configuration
CORS_ORIGINS=https://your-frontend-domain.com,https://sub.your-frontend-domain.com

# Frontend URL (for redirects)
FRONTEND_URL=https://your-frontend-domain.com

# Logging Level
LOG_LEVEL=INFO
```

---

## 🚀 Deployment Steps

### 1. Prepare Your Server

```bash
# SSH into your remote server
ssh user@your-server-ip

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (optional, for non-root usage)
sudo usermod -aG docker $USER
```

### 2. Clone and Configure

```bash
# Clone your repository
git clone <your-repo-url> rhd-estimation
cd rhd-estimation/backend

# Create production environment file
cp .env.prod.template .env.prod

# Generate a strong SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and add it to .env.prod

# Edit .env.prod with your database password and other settings
nano .env.prod
```

### 3. Build and Run

```bash
# Build the Docker image
docker-compose -f docker-compose.prod.yml build

# Start services in background
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend

# View container status
docker-compose -f docker-compose.prod.yml ps
```

### 4. Database Initialization

```bash
# Run database migrations (if using Alembic)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Or if not using Alembic, the app creates tables on startup
docker-compose -f docker-compose.prod.yml logs backend | grep "CREATE"
```

### 5. Nginx Reverse Proxy (Recommended)

Create `nginx.conf`:

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Proxy to FastAPI
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Update `docker-compose.prod.yml` to include Nginx:

```yaml
nginx:
  image: nginx:alpine
  container_name: rhd-estimation-nginx
  restart: always
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
  depends_on:
    - backend
  networks:
    - app-network
```

---

## 🔧 Monitoring & Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Scale Backend (if using load balancer)

```bash
docker-compose up -d --scale backend=3
```

### Backup Database

```bash
docker-compose exec db pg_dump -U $DB_USER $DB_NAME > backup.sql
```

### Restore Database

```bash
docker-compose exec -T db psql -U $DB_USER $DB_NAME < backup.sql
```

---

## 📝 Recommended Security Fixes (Urgent)

1. **Update [app/security.py](app/security.py)**

   ```python
   # Remove default value - require env variable
   SECRET_KEY = os.getenv("SECRET_KEY")
   if not SECRET_KEY:
       raise ValueError("SECRET_KEY environment variable is required")
   ```

2. **Remove .env.production from Git**

   ```bash
   git rm --cached .env.production
   echo ".env.prod" >> .gitignore
   git commit -m "Remove production credentials from version control"
   ```

3. **Add Security Headers Middleware**

   ```python
   from fastapi.middleware import trustedhost
   app.add_middleware(trustedhost.TrustedHostMiddleware, allowed_hosts=[...])
   ```

4. **Add Rate Limiting**

   ```bash
   pip install slowapi
   ```

5. **Add Health Check Endpoint** (critical for Docker)
   ```python
   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}
   ```

---

## ✅ Testing Deployment Locally First

```bash
# Test with docker-compose before deploying
docker-compose up

# Check API is running
curl http://localhost:8000/docs

# Check health endpoint
curl http://localhost:8000/health
```

---

**Next Steps:**

1. Implement security fixes above
2. Generate strong SECRET_KEY
3. Test locally with Docker
4. Deploy to remote server
5. Set up SSL certificates (Let's Encrypt)
6. Monitor logs for errors
