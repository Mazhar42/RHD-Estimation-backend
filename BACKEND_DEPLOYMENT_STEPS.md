# Complete Backend Deployment Step-by-Step Guide

**Purpose:** Deploy your RHD Estimation Backend to your remote server with full CI/CD automation

**Total Setup Time:** 2-3 hours (one-time)  
**Difficulty Level:** Beginner-friendly (just follow the steps)

---

## 📋 Prerequisites Checklist

Before starting, verify you have:

- [ ] **GitHub Account** - Repository created and code pushed
- [ ] **Remote Server** - Linux/Ubuntu server with SSH access
- [ ] **Server Access** - Username, IP address, SSH port number
- [ ] **Local Machine** - GitHub CLI installed (or manual push capability)
- [ ] **Backend Code** - Already in GitHub repository
- [ ] **Terminal/Console** - PowerShell (Windows) or Bash (Mac/Linux)

**Check these now before proceeding:**

```powershell
# Verify you can SSH to server
ssh user@your-server-ip

# Verify git is installed
git --version

# Verify docker exists locally (for testing)
docker --version
```

---

## 🎯 High-Level Deployment Plan

```
Phase 1: Local Preparation (30 minutes)
    └─ Generate SSH keys
    └─ Test SSH connection to server

Phase 2: Remote Server Setup (1 hour)
    └─ SSH into server
    └─ Install Docker & Docker Compose
    └─ Create project directories
    └─ Clone GitHub repository
    └─ Create .env.prod file

Phase 3: GitHub Actions Setup (30 minutes)
    └─ Add GitHub Secrets
    └─ Test first deployment

Phase 4: Verify & Monitor (30 minutes)
    └─ Check deployment logs
    └─ Test API endpoints
    └─ Verify SSL/HTTPS (if applicable)

Total Time: 2.5 - 3 hours
```

---

## 📍 PHASE 1: Local Preparation (30 minutes)

### Step 1.1: Generate SSH Key Pair

**On your local machine**, open PowerShell/Terminal and run:

```powershell
# Navigate to your home directory
cd ~

# Create .ssh directory if it doesn't exist
mkdir .ssh -Force

# Generate SSH key pair (ed25519 is modern and secure)
ssh-keygen -t ed25519 -f ".ssh/github_actions_key" -C "github-actions"

# When prompted for passphrase: LEAVE EMPTY (just press Enter)
# This creates two files:
# - ~/.ssh/github_actions_key (private key - keep secret!)
# - ~/.ssh/github_actions_key.pub (public key - share with server)
```

**Verify the keys were created:**

```powershell
ls ~/.ssh/github_actions_key*

# Should show:
# github_actions_key
# github_actions_key.pub
```

### Step 1.2: Copy Public Key Content

**You'll need this in the next phase:**

```powershell
# Display and copy the public key content (Mac/Linux)
cat ~/.ssh/github_actions_key.pub

# PowerShell (Windows):
Get-Content ~/.ssh/github_actions_key.pub | Set-Clipboard
```

**Save the output somewhere - you'll paste it on the server**

### Step 1.3: Copy Private Key Content

**For GitHub Secrets:**

```powershell
# Display and copy the private key content
cat ~/.ssh/github_actions_key

# PowerShell (Windows):
Get-Content ~/.ssh/github_actions_key | Set-Clipboard
```

**Save this somewhere secure - needs to go in GitHub Secrets**

### ✅ Phase 1 Complete When:

- [ ] SSH key pair generated
- [ ] Public key content copied
- [ ] Private key content saved securely

---

## 🖥️ PHASE 2: Remote Server Setup (1 hour)

### Step 2.1: SSH Into Your Server

**From your local machine:**

```bash
# Replace 'user' with your actual SSH username
# Replace 'your-server-ip' with your actual server IP
ssh -i ~/.ssh/github_actions_key user@your-server-ip

# If this fails, try:
# ssh -i ~/.ssh/github_actions_key -p 22 user@your-server-ip
# (22 is default SSH port - ask your provider if different)
```

**Expected output:** You should be logged into your server terminal

**If connection fails:**

- Check: Is IP address correct?
- Check: Is username correct?
- Check: Is SSH port correct (usually 22)?
- Contact: Your hosting provider for SSH details

### Step 2.2: Update System Packages

**On your server, run:**

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2.3: Install Docker & Docker Compose

**On your server, run:**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (no sudo needed)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 2.4: Create Project Directory

**On your server, run:**

```bash
# Create directory structure
sudo mkdir -p /opt/rhd-estimation
sudo chown $USER:$USER /opt/rhd-estimation

# Create backups directory
mkdir -p /opt/rhd-estimation/backups

# Verify permission
ls -ld /opt/rhd-estimation
```

### Step 2.5: Add Your SSH Public Key to Server

**On your server, run:**

```bash
# Create .ssh directory if needed
mkdir -p ~/.ssh

# Add your PUBLIC key to authorized_keys
# Paste the public key you saved from Step 1.2 here:
cat >> ~/.ssh/authorized_keys << 'EOF'
<PASTE YOUR PUBLIC KEY HERE>
EOF

# Set proper permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Verify
cat ~/.ssh/authorized_keys
```

### Step 2.6: Clone Your GitHub Repository

**On your server, run:**

```bash
cd /opt/rhd-estimation

# Clone your repository
git clone https://github.com/YOUR_USERNAME/your-repo-name.git .

# Verify it worked
ls -la

# Should show: app/, backend/, .github/, etc.
```

**If clone fails:**

- [ ] Check: GitHub username is correct
- [ ] Check: Repository name is correct
- [ ] Check: Repository is public OR you have SSH key on GitHub
- [ ] Solution: Generate GitHub SSH key if needed: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### Step 2.7: Navigate to Backend Directory

**On your server, run:**

```bash
cd /opt/rhd-estimation/backend

# Verify files are there
ls -la

# Should show: Dockerfile, docker-compose.prod.yml, app/, etc.
```

### Step 2.8: Create Environment Configuration File

**On your server, run:**

```bash
# Copy template
cp .env.prod.template .env.prod

# Edit with your actual values
nano .env.prod
```

**In nano editor, fill in these values:**

```env
APP_ENV=production

# REQUIRED: Generate a strong SECRET_KEY
# Run this FIRST on your server: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and paste here:
SECRET_KEY=<paste-generated-key-here>

# Database (choose STRONG password - at least 32 characters)
# Generate with: openssl rand -base64 32
DB_USER=rhd_estimation_user
DB_PASSWORD=<paste-strong-password-here>
DB_HOST=db
DB_PORT=5432
DB_NAME=rhd_estimation
DATABASE_URL=postgresql://rhd_estimation_user:<same-password-as-above>@db:5432/rhd_estimation

# CORS - your frontend domain
CORS_ORIGINS=https://your-frontend-domain.vercel.app

# API runs on localhost on server (Nginx reverse proxy handles external access)
```

**To save and exit nano:**

1. Press `Ctrl + X`
2. Press `Y` (yes to save)
3. Press `Enter` (confirm filename)

### Step 2.9: Generate Strong Passwords/Keys

**On your server, run before filling .env.prod:**

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate Database Password
openssl rand -base64 32
```

**Save both outputs and add to .env.prod**

### Step 2.10: Verify Environment File

**On your server, run:**

```bash
cat .env.prod

# Should show all variables filled in
# Important: Never commit this file to GitHub!
git check-ignore .env.prod  # Should return: .env.prod (already ignored)
```

### Step 2.11: Create Initial Docker Containers

**On your server, run:**

```bash
cd /opt/rhd-estimation/backend

# This will take 5-10 minutes first time
docker-compose -f docker-compose.prod.yml up -d

# Check if containers started
docker-compose -f docker-compose.prod.yml ps

# Should show 3 containers: db, backend, nginx
```

### Step 2.12: Wait for Database to Be Ready

**On your server, run:**

```bash
# Wait about 30 seconds, then check:
docker-compose -f docker-compose.prod.yml logs db

# Should see "database system is ready to accept connections"
```

### Step 2.13: Verify API is Responding

**On your server, run:**

```bash
# Check if backend is healthy
curl http://localhost:8000/health

# Should return something like:
# {"status":"healthy","service":"estimation-backend","version":"1.0.0"}

# If it fails, check logs:
docker-compose -f docker-compose.prod.yml logs backend
```

### ✅ Phase 2 Complete When:

- [ ] SSH connection successful
- [ ] Docker & Docker Compose installed
- [ ] Project directory created at `/opt/rhd-estimation`
- [ ] Repository cloned
- [ ] `.env.prod` created with all values
- [ ] Containers running (3 show in `ps`)
- [ ] Health check returns 200 OK

---

## 🔐 PHASE 3: GitHub Actions CI/CD Setup (30 minutes)

### Step 3.1: Add GitHub Secrets

**In your browser:**

1. Go to: **GitHub.com → Your Repository**
2. Click: **Settings** (top menu)
3. Click: **Secrets and variables** (left sidebar)
4. Click: **Actions** (submenu)
5. Click: **New repository secret**

### Step 3.2: Add Secret #1: SSH_PRIVATE_KEY

**In GitHub Secrets UI:**

1. **Name:** `SSH_PRIVATE_KEY`
2. **Secret:** Paste entire content of `~/.ssh/github_actions_key` (the private key saved in Step 1.3)
3. Click: **Add secret**

### Step 3.3: Add Secret #2: SERVER_IP

**In GitHub Secrets UI:**

1. **Name:** `SERVER_IP`
2. **Secret:** Your server's IP address (e.g., `203.0.113.42`)
3. Click: **Add secret**

### Step 3.4: Add Secret #3: SERVER_USER

**In GitHub Secrets UI:**

1. **Name:** `SERVER_USER`
2. **Secret:** Your SSH username (e.g., `ubuntu`, `root`, `ec2-user`)
3. Click: **Add secret**

### Step 3.5: Verify All Three Secrets Are Added

**In GitHub Secrets UI:**

You should see:

- ✅ SSH_PRIVATE_KEY
- ✅ SERVER_IP
- ✅ SERVER_USER

**Status:** (Shown as dots for security)

---

## 🧪 PHASE 4: Test First Deployment (30 minutes)

### Step 4.1: Make a Test Commit Locally

**On your local machine:**

```bash
# Navigate to your project
cd ~/your-repo-directory

# Make a small test change
echo "# Test deployment on $(date)" >> backend/README.md

# Check what changed
git status

# Stage the change
git add backend/README.md

# Commit
git commit -m "test: trigger CI/CD deployment pipeline"

# Push to GitHub (main or master branch)
git push origin main
# or
git push origin master
```

### Step 4.2: Watch GitHub Actions Run

**In your browser:**

1. Go to your GitHub repository
2. Click: **Actions** tab (top menu)
3. Click: The latest workflow run (at the top)
4. Watch the pipeline execute in real-time!

**You should see:**

- ✅ **Test & Build** job running (~5 minutes)
- ✅ **Deploy** job starts (~2 minutes wait)
- ✅ **Deploy** job runs SSH commands (~5 minutes)

**Entire deployment:** ~12 minutes total

### Step 4.3: Monitor Deployment Progress

**In GitHub Actions UI:**

Click on **"Deploy"** job to see detailed logs:

- `$ Checkout code`
- `$ Deploy via SSH`
- `...git pull...`
- `...docker build...`
- `...health check...`

**Green checkmarks** = Success ✅  
**Red X marks** = Failed ❌

### Step 4.4: Check Server Logs During Deployment

**On your server (different terminal):**

```bash
# SSH into server
ssh user@your-server-ip

# Watch deployment log in real-time
cd /opt/rhd-estimation/backend
tail -f /opt/rhd-estimation/deployment.log

# Or check Docker logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Step 4.5: Verify Deployment Succeeded

**After ~12 minutes:**

**Check 1: GitHub Actions shows green checkmark**

- Go to GitHub → Actions tab
- Latest workflow should have green ✅

**Check 2: API responds on server**

```bash
# On server:
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"estimation-backend","version":"1.0.0"}
```

**Check 3: Docker containers are running**

```bash
# On server:
docker-compose -f docker-compose.prod.yml ps

# Should show:
# NAME              STATUS
# db                Up 12 minutes
# backend           Up 12 minutes
# nginx             Up 12 minutes
```

**Check 4: No errors in logs**

```bash
# On server:
docker-compose -f docker-compose.prod.yml logs --tail=50

# Should show no ERROR messages
```

### ✅ Phase 4 Complete When:

- [ ] Test commit pushed to GitHub
- [ ] GitHub Actions workflow completed (green ✅)
- [ ] API health check returns 200 OK
- [ ] All 3 Docker containers running
- [ ] Deployment took ~12 minutes
- [ ] No ERROR messages in logs

---

## 🎉 SUCCESS: Your Backend is Deployed!

### What Just Happened

```
Your laptop:
  git push origin main  ← You run this
    ↓
GitHub:
  Workflow triggered
    ├─ Test & Build (5 min)
    └─ Deploy (7 min)
    ↓
Your Server:
  Pulled code
  Built Docker image
  Started containers
  Ran health checks ✅
    ↓
API is LIVE! 🎉
```

---

## 📊 Next Steps: From Now On

### Future Deployments (Automatic!)

**All you need to do:**

```bash
# Make code changes
code app/main.py

# Commit
git commit -m "feat: add new endpoint"

# Push
git push origin main

# ✨ Automatic deployment happens in ~12 minutes
# No manual SSH needed anymore!
```

### Monitor Deployments

```bash
# Check GitHub Actions (most convenient)
# GitHub UI → Actions tab → Latest run

# Or check server logs
ssh user@your-server-ip
tail -f /opt/rhd-estimation/deployment.log
```

### Verify After Each Deployment

```bash
# Quick health check
curl http://localhost:8000/health

# Check containers
docker-compose -f docker-compose.prod.yml ps
```

---

## 🆘 Troubleshooting

### Problem: GitHub Actions Workflow Not Triggering

**Check:**

1. Did you push to `main` or `master` branch?
2. Is branch name correct? (case-sensitive!)
3. Are workflow files in `.github/workflows/`?

**Solution:**

```bash
# View all branches
git branch -a

# Make sure you're on main
git checkout main

# Push again
git push origin main
```

---

### Problem: "Permission Denied" SSH Error

**Check:**

1. Is SSH_PRIVATE_KEY correct in GitHub Secrets?
2. Is SERVER_IP correct?
3. Is SERVER_USER correct?

**Solution:**

```bash
# Verify locally that SSH works
ssh -i ~/.ssh/github_actions_key user@your-server-ip "echo 'Success!'"

# If it works locally, GitHub Actions will work too
```

---

### Problem: "Health Check Failed"

**Check:**

1. Are containers running? `docker-compose ps`
2. Are there errors? `docker-compose logs backend`
3. Is database ready? `docker-compose logs db`

**Solution:**

```bash
# SSH to server
ssh user@your-server-ip

# Check logs
cd /opt/rhd-estimation/backend
docker-compose -f docker-compose.prod.yml logs -f

# Restart if needed
docker-compose -f docker-compose.prod.yml restart
```

---

### Problem: Database Connection Error

**Solution:**

```bash
# Check if .env.prod has correct password
cat /opt/rhd-estimation/backend/.env.prod

# Verify database password matches in DATABASE_URL
# Format: postgresql://USER:PASSWORD@HOST:PORT/DBNAME

# Restart database
docker-compose -f docker-compose.prod.yml restart db

# Wait 20 seconds then check
sleep 20
curl http://localhost:8000/health
```

---

## 📚 Reference Documentation

| Need                | File                                    |
| ------------------- | --------------------------------------- |
| Quick commands      | QUICK_REFERENCE.md                      |
| Detailed setup help | CICD_SETUP.md                           |
| How CI/CD works     | CICD_ARCHITECTURE.md                    |
| Troubleshooting     | CICD_SETUP.md (Troubleshooting section) |
| Docker issues       | DOCKER_DEPLOYMENT_GUIDE.md              |
| Security info       | SECURITY_AUDIT_REPORT.md                |

---

## ✨ You're Done!

**Your FastAPI backend is now:**

✅ Deployed to your remote server  
✅ Running in Docker containers  
✅ Automatically deployed on every GitHub push  
✅ Protected by database backups  
✅ Health-checked automatically  
✅ Monitored with logs  
✅ Production-ready!

**From now on: Just push code to GitHub → Automatic deployment! 🚀**

---

## 📝 Deployment Checklist (For Future Reference)

Save this for deploying updates:

```
□ Make code changes locally
□ Test with: docker-compose up
□ Commit: git commit -m "..."
□ Push: git push origin main
□ Monitor: GitHub Actions tab
□ Wait: ~12 minutes for deployment
□ Verify: curl http://localhost:8000/health
□ Celebrate: Changes are live! 🎉
```

---

**Question? First check:**

1. GitHub Actions logs (most detailed)
2. Server deployment log: `tail -f /opt/rhd-estimation/deployment.log`
3. Docker logs: `docker-compose logs backend`
4. Reference docs in `DOCUMENTATION.md`
