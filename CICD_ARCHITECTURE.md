# CI/CD Pipeline Architecture & Integration

Complete overview of the automated deployment system.

---

## 🏗️ Architecture Diagram

```
Developer's Computer
    │
    └─→ git push origin main
         │
         ↓
GitHub Repository
    │
    ├─→ .github/workflows/deploy.yml (triggered on push to main)
    │
    └─→ GitHub Actions Runners (Ubuntu Latest)
         │
         ├─ Job 1: Test & Build
         │   ├─ Checkout code
         │   ├─ Setup Python 3.11
         │   ├─ Install dependencies
         │   ├─ Run syntax checks
         │   ├─ Run tests (if available)
         │   └─ Build Docker image
         │
         ├─ Job 2: Deploy (depends on Job 1 success)
         │   │
         │   └─→ SSH to Remote Server (203.0.113.42)
         │       │
         │       ├─ Pull latest code from GitHub
         │       ├─ Build Docker image on server
         │       ├─ Backup PostgreSQL database
         │       ├─ Stop old containers
         │       ├─ Start new containers
         │       └─ Run health checks
         │
         └─→ Job 3: Notification (optional, Slack)
             ├─ Success → Slack message
             └─ Failure → Slack message

Remote Server (Your VPS)
    │
    ├─ /opt/rhd-estimation/
    │   ├─ backend/
    │   │   ├─ app/
    │   │   ├─ docker-compose.prod.yml
    │   │   ├─ .env.prod
    │   │   └─ .github/workflows/
    │   │
    │   └─ backups/
    │       └─ backup-20260307-120000.sql
    │
    ├─ Docker Containers
    │   ├─ PostgreSQL 16 (database)
    │   ├─ FastAPI Backend (your app)
    │   └─ Nginx (reverse proxy)
    │
    └─ Health Check: curl http://localhost:8000/health
         │
         └─→ GitHub Actions sees response
             └─→ Deployment successful ✅
```

---

## 📊 Workflow Execution Timeline

### When You Push Code to Main Branch

```
Time: 00:00s  → Code pushed to GitHub
Time: 00:05s  → GitHub Actions workflow starts
Time: 00:15s  → Dependencies installed
Time: 00:30s  → Tests run
Time: 00:45s  → Docker image built (5-10 min typically)
Time: 10:00s → SSH connection to server established
Time: 10:10s → Code pulled on server
Time: 10:20s → Docker image built on server
Time: 10:30s → Database backed up
Time: 10:40s → Old containers stopped
Time: 10:50s → New containers started
Time: 11:00s → Health checks running
Time: 11:30s → ✅ DEPLOYMENT SUCCESSFUL
```

**Total Time:** ~11.5 minutes (varies by server performance)

---

## 🔄 How It All Works Together

### 1. Local Development (Your Computer)

```bash
# You make changes locally
code app/main.py

# Test locally
docker-compose up

# When happy, push to GitHub
git push origin feature/my-change

# Create Pull Request (optional but recommended)
# GitHub runs validation checks
# Get feedback from team
```

### 2. Pull Request (GitHub UI)

```
Pull Request opened
    ↓
GitHub Actions runs:
  - Syntax checks
  - Security scans
  - Code quality checks
  - Docker build validation
    ↓
Comment on PR with results
    ↓
You review feedback
    ↓
Make additional commits if needed
```

### 3. Merge & Deploy (GitHub UI)

```
Merge PR to main/master
    ↓
Automatically triggers: .github/workflows/deploy.yml
    ↓
Runs Test & Build job
    ↓
Runs Deploy job (on success)
    ↓
Sends Slack notification
```

### 4. Remote Server (Automatic)

```
Receives SSH connection from GitHub Actions
    ↓
Pulls latest code
    ↓
Builds new Docker image
    ↓
Backs up database
    ↓
Stops old containers
    ↓
Starts new containers
    ↓
Runs health checks
    ↓
You see updated website/API
```

---

## 📁 File Structure

### Created Files for CI/CD

```
your-repo/
├── .github/
│   └── workflows/
│       ├── deploy.yml
│       │   ├─ Triggers: on push to main/master
│       │   ├─ Runs tests
│       │   ├─ Builds Docker image
│       │   └─ Deploys via SSH
│       │
│       ├── security.yml
│       │   ├─ Runs on push/PR
│       │   ├─ Checks for hardcoded secrets
│       │   ├─ Scans dependencies
│       │   └─ Lints code
│       │
│       └── validate.yml
│           ├─ Runs on PR
│           ├─ Checks for .env files
│           ├─ Validates Docker configs
│           └─ Checks for debug code
│
├── scripts/
│   └── deploy-remote.sh
│       ├─ Runs on remote server
│       ├─ Pulls code
│       ├─ Builds Docker image
│       ├─ Manages containers
│       └─ Health checks
│
└── backend/
    ├── Dockerfile
    ├── docker-compose.yml
    ├── docker-compose.prod.yml
    └── .env.prod (not in repo!)
```

---

## 🔐 GitHub Secrets Configuration

These are secrets only you and GitHub know:

```
GitHub Repository Settings
    └─ Secrets and variables
        └─ Actions
            ├─ SSH_PRIVATE_KEY (private SSH key)
            ├─ SERVER_IP (server IP address)
            ├─ SERVER_USER (SSH username)
            └─ SLACK_WEBHOOK_URL (optional)
```

**Inside deploy.yml:**

```yaml
uses: appleboy/ssh-action@master
with:
  host: ${{ secrets.SERVER_IP }} # GitHub substitutes actual IP
  username: ${{ secrets.SERVER_USER }} # GitHub substitutes username
  key: ${{ secrets.SSH_PRIVATE_KEY }} # GitHub substitutes private key
```

---

## 🚨 Security Considerations

### What's Protected

✅ SSH private key - only exists in GitHub encrypted storage
✅ Database password - only in .env.prod on server
✅ SECRET_KEY - only in .env.prod on server
✅ API keys/tokens - never committed to git

### What's Public

📖 Source code - GitHub repository visible
📖 Workflow files - automation visible
📖 Docker setup - container config visible
📖 API endpoints - public API documentation

### Best Practices Implemented

- ✅ No credentials in code
- ✅ Environment files in .gitignore
- ✅ SSH key-based authentication
- ✅ Automatic database backups
- ✅ Health checks before marking deployment successful
- ✅ Security scans on every PR
- ✅ Code quality checks

---

## 🛠️ Integrations

### GitHub Actions Integrations

```
.github/workflows/deploy.yml
    │
    ├─→ appleboy/ssh-action
    │   └─ SSH into your server
    │
    ├─→ slackapi/slack-github-action (optional)
    │   ├─ Send success notification
    │   └─ Send failure notification
    │
    └─→ actions/checkout
        └─ Download your code
```

### Docker Integration

```
deploy.yml (GitHub Actions)
    │
    └─→ docker build .
        └─ Builds: ghcr.io/username/app:sha

deploy-remote.sh (Server)
    │
    └─→ docker-compose up -d
        ├─ PostgreSQL container
        ├─ FastAPI container
        └─ Nginx container
```

### Database Integration

```
deploy-remote.sh (Server)
    │
    ├─→ pg_dump → SQL backup file
    │   └─ /opt/rhd-estimation/backups/backup-*.sql
    │
    └─→ docker-compose.prod.yml
        └─ Manages PostgreSQL container
```

---

## 📊 Branch Strategy

### Recommended Workflow

```
main/master (production)
    ↑
    │ (deploy.yml triggers here)
    │
develop (staging/testing)
    ↑
    │
feature branches (your work)
└─ feature/auth-fix
└─ feature/new-endpoint
└─ feature/performance-improvements
```

### Deployment Trigger Points

| Branch    | Trigger    | Action                |
| --------- | ---------- | --------------------- |
| main      | push       | Deploy to production  |
| master    | push       | Deploy to production  |
| Any other | push       | Run tests only        |
| PR        | any branch | Run validation checks |

---

## 🔄 Rollback Procedure

If deployment goes wrong:

### Automatic Rollback (Database)

```bash
# Database backup is created before every deployment
ls /opt/rhd-estimation/backups/

# Restore if something goes wrong
docker-compose -f docker-compose.prod.yml exec -T db \
  psql -U rhd_estimation_user -d rhd_estimation < backups/backup-20260307-120000.sql
```

### Manual Rollback

```bash
# SSH into server
ssh user@your-server-ip

# Stop current deployment
cd /opt/rhd-estimation/backend
docker-compose -f docker-compose.prod.yml down

# Reset to previous commit
git reset --hard HEAD~1

# Restart
docker-compose -f docker-compose.prod.yml up -d
```

### Disable Auto-Deploy

```bash
# Temporarily disable deploy workflow
# Go to Actions → Deploy → Edit → Disable
# Or delete the workflow file temporarily
```

---

## 📈 Monitoring & Logging

### GitHub Actions Logs

```
GitHub → Actions → Click workflow run → View logs
    │
    ├─ Test & Build job
    ├─ Deploy job
    └─ Notification job
```

### Server Deployment Log

```
SSH to server
cd /opt/rhd-estimation
tail -f deployment.log
```

### Docker Logs

```
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f db
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### API Health Check

```
curl http://localhost:8000/health
    ↓
{
  "status": "healthy",
  "service": "estimation-backend",
  "version": "1.0.0"
}
```

---

## 🎯 Common Scenarios

### Scenario 1: Bug Fix

```
1. Pull latest code locally
2. Fix bug in app/main.py
3. Test with: docker-compose up
4. git push origin feature/bug-fix
5. Create PR on GitHub
6. GitHub runs checks
7. Merge to main
8. ~11 minutes later → deployed ✅
```

### Scenario 2: New Feature

```
1. Create feature branch: git checkout -b feature/new-api
2. Implement endpoint
3. Add tests if available
4. Local testing
5. Push and create PR
6. Team reviews
7. Make requested changes
8. Merge when approved
9. GitHub Actions deploys automatically ✅
```

### Scenario 3: Emergency Hotfix

```
1. If deploy is critical:
   git pull origin main
   Fix bug
   git push origin main
   (Deploy immediately starts)

2. Monitor: GitHub Actions tab
3. Check: tail -f /opt/rhd-estimation/deployment.log
4. Verify: curl http://localhost:8000/health
```

### Scenario 4: Scheduled Jobs

```
# Create custom schedule in GitHub Actions
on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday at midnight

# Run maintenance tasks
```

---

## 📚 Documentation Files

| File                           | Purpose                         |
| ------------------------------ | ------------------------------- |
| CICD_SETUP.md                  | Step-by-step setup instructions |
| .github/workflows/deploy.yml   | Deployment workflow             |
| .github/workflows/security.yml | Security checks                 |
| .github/workflows/validate.yml | PR validation                   |
| scripts/deploy-remote.sh       | Server-side script              |

---

## 🚀 Performance Tips

### Speed Up Deployment

1. **Use caching:**

   ```yaml
   - uses: actions/setup-python@v4
     with:
       python-version: "3.11"
       cache: "pip" # Cache pip dependencies
   ```

2. **Parallel jobs:** Jobs run concurrently

   ```yaml
   security-check:
     runs-on: ubuntu-latest

   code-quality:
     runs-on: ubuntu-latest

   # Both run at same time (~2 min)
   ```

3. **Skip unnecessary steps:**
   ```yaml
   - name: Run tests
     if: github.event_name == 'pull_request'
     # Only run on PRs, not on push
   ```

---

## ✨ Key Benefits

✅ **Automated:** One-command deployment - just push code  
✅ **Consistent:** Same process every time  
✅ **Safe:** Tests run before deployment  
✅ **Reversible:** Database backups before each deploy  
✅ **Visible:** All logs available in GitHub Actions  
✅ **Notified:** Slack notifications (optional)  
✅ **Scalable:** Easy to add more servers  
✅ **Secure:** SSH keys, encrypted secrets

---

## ❓ FAQ

**Q: How long does deployment take?**
A: ~11.5 minutes total (varies by server performance)

**Q: Can I deploy without going through CI/CD?**
A: Yes, SSH to server and run manually, but not recommended for production

**Q: What if deployment fails?**
A: Database is backed up. Check logs, fix issue, push new commit

**Q: Can multiple people deploy at once?**
A: Workflows queue - they run sequentially to avoid conflicts

**Q: How do I rollback to previous version?**
A: `git reset --hard previous-commit` on server

**Q: Can I deploy from a branch other than main?**
A: Edit `.github/workflows/deploy.yml` to add more branches

---

Now you have a complete automated CI/CD system! 🎉

For detailed setup instructions, see: **CICD_SETUP.md**
