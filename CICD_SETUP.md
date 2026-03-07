# GitHub Actions CI/CD Pipeline Setup

Complete guide to set up automated deployment from GitHub to your remote server.

---

## 📋 Overview

The CI/CD pipeline automatically:

1. Tests your code when you push to GitHub
2. Builds a Docker image
3. Deploys to your remote server via SSH
4. Runs health checks
5. Notifies you of success/failure

**Trigger:** Push to `main` or `master` branch → Automatic deployment  
**Files Changed:** 4 workflow files + 1 deployment script

---

## 🔐 Step 1: Generate SSH Keys

### On Your Local Machine

```bash
# Generate SSH key pair (leave passphrase empty for CI/CD)
ssh-keygen -t ed25519 -f github_actions_key -C "github-actions"

# You'll see two files:
# - github_actions_key (private key)
# - github_actions_key.pub (public key)
```

### Copy Public Key to Your Server

```bash
# Option 1: If you have password SSH access
ssh-copy-id -i github_actions_key.pub user@your-server-ip

# Option 2: Manual method - SSH to server and add key
cat github_actions_key.pub | ssh user@your-server-ip "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# Verify it works
ssh -i github_actions_key user@your-server-ip "echo 'SSH connection successful'"
```

---

## 🔑 Step 2: Add GitHub Secrets

### Go to GitHub Repository Settings

1. Navigate to: **Settings → Secrets and variables → Actions**
2. Click **"New repository secret"** and add these:

| Secret Name         | Value                            | Notes                        |
| ------------------- | -------------------------------- | ---------------------------- |
| `SSH_PRIVATE_KEY`   | Contents of `github_actions_key` | Keep this private!           |
| `SERVER_IP`         | Your server's IP address         | e.g., `203.0.113.42`         |
| `SERVER_USER`       | SSH username                     | e.g., `ubuntu`, `root`       |
| `SLACK_WEBHOOK_URL` | (Optional) Slack webhook         | For deployment notifications |

### How to Add a Secret

1. Click **"New repository secret"**
2. Name: `SSH_PRIVATE_KEY`
3. Secret: Copy entire contents of your `github_actions_key` file
4. Click **"Add secret"**

**Repeat for all secrets above**

---

## 🖥️ Step 3: Prepare Your Remote Server

### SSH into Your Server

```bash
ssh user@your-server-ip
```

### Create Project Directory

```bash
# Create directory structure
sudo mkdir -p /opt/rhd-estimation
cd /opt/rhd-estimation

# Set proper permissions
sudo chown $USER:$USER /opt/rhd-estimation
sudo chmod 755 /opt/rhd-estimation
```

### Clone Your Repository

```bash
cd /opt/rhd-estimation

# Clone your GitHub repository
git clone https://github.com/YOUR_USERNAME/your-repo.git .

# Initialize git if cloning
cd backend
git config user.email "github-actions@yourcompany.com"
git config user.name "GitHub Actions"
```

### Create Production Environment File

```bash
cd /opt/rhd-estimation/backend

# Copy template
cp .env.prod.template .env.prod

# Edit with your actual values
nano .env.prod
```

**Required values in .env.prod:**

```env
APP_ENV=production
SECRET_KEY=your-strong-secret-key-here
DB_USER=rhd_estimation_user
DB_PASSWORD=your-strong-password
DB_HOST=db
DB_PORT=5432
DB_NAME=rhd_estimation
DATABASE_URL=postgresql://rhd_estimation_user:your-strong-password@db:5432/rhd_estimation
```

### Create Backups Directory

```bash
mkdir -p /opt/rhd-estimation/backups
chmod 755 /opt/rhd-estimation/backups
```

### Configure Git Deployment Key

```bash
cd /opt/rhd-estimation

# Allow GitHub Actions to pull code
# Option 1: Use HTTPS with Personal Access Token
git remote set-url origin https://YOUR_GITHUB_TOKEN@github.com/YOUR_USERNAME/your-repo.git

# Option 2: Use SSH (recommended)
git remote set-url origin git@github.com:YOUR_USERNAME/your-repo.git
```

---

## 🚀 Step 4: Test the CI/CD Pipeline

### Make a Test Commit

```bash
# Locally, make a small change
echo "# Updated $(date)" >> backend/README.md

# Commit and push
git add backend/README.md
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

### Monitor the Deployment

1. Go to **GitHub → Actions** tab
2. Click on the latest workflow run
3. Watch the pipeline execute in real-time

---

## 📊 CI/CD Workflow Breakdown

### GitHub Workflows Created

```
.github/workflows/
├── deploy.yml          # Main deployment workflow (runs on push to main)
├── security.yml        # Security & code quality checks (runs on push/PR)
└── validate.yml        # Validation checks (runs on PRs)
```

### Deployment Steps

1. **Test & Build** (GitHub Actions runner)
   - Checkout code
   - Setup Python 3.11
   - Install dependencies
   - Run syntax checks
   - Run tests (if available)
   - Build Docker image

2. **Deploy** (Your remote server via SSH)
   - Connect via SSH
   - Pull latest code
   - Build Docker image
   - Backup database
   - Stop old containers
   - Start new containers
   - Run health checks

3. **Notification** (Optional)
   - Send Slack message on success
   - Send Slack message on failure

---

## 🔍 Monitoring Deployments

### GitHub Actions Dashboard

1. Go to **Actions** tab in your repository
2. View all workflow runs
3. Click on a run to see detailed logs

### View Deployment Logs on Server

```bash
# SSH into server
ssh user@your-server-ip

# View Docker logs
cd /opt/rhd-estimation/backend
docker-compose -f docker-compose.prod.yml logs -f backend

# View deployment log
tail -f /opt/rhd-estimation/deployment.log
```

### Health Check

```bash
# Check if API is running
curl -s http://localhost:8000/health | python3 -m json.tool

# Should return:
# {
#   "status": "healthy",
#   "service": "estimation-backend",
#   "version": "1.0.0"
# }
```

---

## 📋 Status Checks Explained

### ✅ When Deployment Succeeds

- All tests pass
- Docker image builds
- SSH connection successful
- Containers start
- Health checks pass
- API is responding

### ❌ When Deployment Fails

- Code syntax errors
- Test failures
- Docker build fails
- SSH connection fails
- Database connection fails
- Health check timeout

**Check logs:** Click the failed step in GitHub Actions

---

## 🔄 Typical Workflow

### For Daily Development

```bash
# 1. Clone repository locally
git clone https://github.com/YOUR_USERNAME/your-repo.git
cd backend

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes
nano app/main.py

# 4. Test locally
docker-compose up

# 5. Commit changes
git add app/main.py
git commit -m "feat: add new feature"

# 6. Push to GitHub
git push origin feature/my-feature

# 7. Create Pull Request on GitHub
# - GitHub runs checks (security, code quality, Docker build)
# - Review feedback in PR

# 8. Merge to main
# - GitHub Actions automatically deploys to production
# - Check deployment status in Actions tab
# - Monitor server with: tail -f /opt/rhd-estimation/deployment.log
```

---

## 📝 Environment Variables in CI/CD

### GitHub Secrets Used

| Secret              | Used For                 | Example                       |
| ------------------- | ------------------------ | ----------------------------- |
| `SSH_PRIVATE_KEY`   | Authentication to server | Private key content           |
| `SERVER_IP`         | Server address           | `203.0.113.42`                |
| `SERVER_USER`       | SSH username             | `ubuntu`                      |
| `SLACK_WEBHOOK_URL` | Notifications            | `https://hooks.slack.com/...` |

### Server Environment Variables

Stored in `/opt/rhd-estimation/backend/.env.prod`:

- `SECRET_KEY` - JWT secret
- `DATABASE_URL` - PostgreSQL connection
- `APP_ENV` - Always `production`
- `DB_USER`, `DB_PASSWORD` - Database credentials

---

## 🛡️ Security Best Practices

1. **Never commit .env files** ❌

   ```bash
   # Already in .gitignore
   .env
   .env.prod
   .env.production
   ```

2. **Rotate SSH keys periodically** 🔑

   ```bash
   # Generate new key and update server
   ssh-keygen -t ed25519 -f github_actions_key_v2
   ssh-copy-id -i github_actions_key_v2.pub user@server
   ```

3. **Use strong DATABASE_PASSWORD** 🔐
   - At least 32 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - Generate: `openssl rand -base64 32`

4. **Limit SSH key permissions** 🚫

   ```bash
   # On server
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```

5. **Monitor deployment logs** 📊
   - Review failed deployments immediately
   - Check health check results
   - Monitor database backups

---

## 🐛 Troubleshooting

### "Permission denied (publickey)"

```
Problem: SSH key not authorized on server
Solution:
1. Verify public key in ~/.ssh/authorized_keys
2. Check SSH file permissions (should be 600)
3. Regenerate and re-add the key
```

### "Database backup failed"

```
Problem: Database not accessible during deployment
Solution:
1. First deployment - backup will be skipped (expected)
2. Subsequent - check if db container is running
3. Verify DB_USER and DB_NAME in .env.prod
```

### "Health check timeout"

```
Problem: Backend container not ready
Solution:
1. Check Docker build: docker-compose logs backend
2. Wait 30 seconds - containers need time to start
3. Verify health endpoint: curl http://localhost:8000/health
```

### "Git pull failed"

```
Problem: Repository access issue
Solution:
1. Verify SSH key is added to GitHub repo deploy keys (or use personal access token)
2. Check branch name (main vs master)
3. Ensure repository is public or deploy key has access
```

### Workflow not triggering

```
Problem: Push to main doesn't start deployment
Solution:
1. Check workflow file syntax: .github/workflows/deploy.yml
2. Verify GitHub branch is "main" or "master" (case-sensitive)
3. Check branch protection rules - may require PR approval
4. Look at Actions tab for any errors
```

---

## 📈 Advanced Configuration

### Add Slack Notifications

1. Create Slack Webhook:
   - Go to Slack Workspace → Settings
   - Apps → Custom Integrations → Incoming WebHooks
   - Copy webhook URL

2. Add Secret to GitHub:
   - Settings → Secrets → New secret
   - Name: `SLACK_WEBHOOK_URL`
   - Value: Your webhook URL

3. Already configured in `deploy.yml` - just set the secret!

### Run Tests Before Deploy

The workflow includes test steps, but they're marked `continue-on-error: true` so failures don't block deployment.

To make them required:

```yaml
# Edit .github/workflows/deploy.yml
- name: Run tests
  run: pytest -v
  # Remove continue-on-error line - now tests MUST pass
```

### Deploy Only Specific Branches

Edit `.github/workflows/deploy.yml`:

```yaml
on:
  push:
    branches:
      - main # Only main branch
      - staging # Add staging branch
```

### Add Approval Required Before Deploy

Use GitHub branch protection rules:

1. Settings → Branches
2. Add rule for `main`
3. Require approving review before deployment

---

## 📋 Checklist for CI/CD Setup

- [ ] Generated SSH key pair
- [ ] Added public key to server
- [ ] Added Secret: `SSH_PRIVATE_KEY`
- [ ] Added Secret: `SERVER_IP`
- [ ] Added Secret: `SERVER_USER`
- [ ] Created `/opt/rhd-estimation` directory on server
- [ ] Cloned repository to server
- [ ] Created `.env.prod` file on server
- [ ] Verified git can pull on server
- [ ] Made test commit and verified deployment
- [ ] Checked GitHub Actions logs
- [ ] Verified health check on server
- [ ] Tested database backup
- [ ] (Optional) Added Slack notifications

---

## 📚 Files Created

```
.github/
├── workflows/
│   ├── deploy.yml              # Main deployment pipeline
│   ├── security.yml            # Security & code quality checks
│   └── validate.yml            # PR validation checks
└── README.md

scripts/
└── deploy-remote.sh            # Server-side deployment script
```

---

## 🚀 Quick Command Reference

### On Your Local Machine

```bash
# Test locally before pushing
docker-compose up

# Push changes
git push origin main

# Check deployment status
# Go to: GitHub → Actions tab
```

### On Your Server

```bash
# Connect to server
ssh user@your-server-ip

# View deployment logs
tail -f /opt/rhd-estimation/deployment.log

# Check container status
cd /opt/rhd-estimation/backend
docker-compose -f docker-compose.prod.yml ps

# View application logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Manual restart if needed
docker-compose -f docker-compose.prod.yml restart
```

---

## ℹ️ Important Notes

1. **First deployment:** Will fail if `.env.prod` is not set up correctly
2. **Database backup:** Only works after first successful deployment
3. **Health checks:** May need up to 30 seconds for containers to be ready
4. **SSH timeout:** Default 10 minutes - increase if deployment takes longer
5. **Log retention:** GitHub Actions keeps logs for 90 days

---

## 🎯 Next Steps

1. **TODAY:**
   - [ ] Generate SSH keys
   - [ ] Add GitHub Secrets
   - [ ] Prepare server directory

2. **THIS WEEK:**
   - [ ] Clone repo to server
   - [ ] Create `.env.prod`
   - [ ] Test first deployment

3. **ONGOING:**
   - [ ] Monitor deployments
   - [ ] Review logs
   - [ ] Update as needed

---

For issues, check:

1. GitHub Actions logs (most detailed)
2. Server deployment log: `/opt/rhd-estimation/deployment.log`
3. Docker container logs: `docker-compose logs backend`

Good luck with your automated deployment! 🚀
