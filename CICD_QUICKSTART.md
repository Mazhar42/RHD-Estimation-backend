# 🚀 CI/CD Quick Start (5 Minutes)

Get automated deployments working in 5 steps.

---

## ✨ What You'll Get

When you're done, pushing code to GitHub will **automatically**:

- ✅ Run tests
- ✅ Build Docker image
- ✅ Deploy to your server
- ✅ Run health checks
- ✅ Notify you on success/failure

---

## 📋 Prerequisites

- GitHub account with a repository
- Remote server with SSH access
- Docker & Docker Compose on server
- Project already set up with Docker (previous guides)

---

## 🔑 Step 1: Generate SSH Key (2 minutes)

**On your local machine:**

```bash
# Generate SSH key (press Enter when asked for passphrase)
ssh-keygen -t ed25519 -f github_actions_key -C "github-actions"

# This creates two files:
# - github_actions_key (PRIVATE - keep secret!)
# - github_actions_key.pub (PUBLIC - share with server)
```

**Verify files exist:**

```bash
ls -la github_actions_key*
```

---

## 🔐 Step 2: Add Key to Server (2 minutes)

**Option A: If you have password access**

```bash
ssh-copy-id -i github_actions_key.pub user@your-server-ip
```

**Option B: Manual add**

```bash
# SSH to server
ssh user@your-server-ip

# Add the key
mkdir -p ~/.ssh
cat >> ~/.ssh/authorized_keys << 'EOF'
<paste content of github_actions_key.pub here>
EOF

# Set permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

**Test it works:**

```bash
ssh -i github_actions_key user@your-server-ip "echo 'Success!'"
```

---

## 🔑 Step 3: Add GitHub Secrets (2 minutes)

**Go to GitHub:**

1. Open your repository
2. **Settings → Secrets and variables → Actions**
3. Click **"New repository secret"**

**Add these 3 secrets:**

### Secret #1: SSH_PRIVATE_KEY

- Name: `SSH_PRIVATE_KEY`
- Value: Copy entire content of `github_actions_key` file
- Click **"Add secret"**

### Secret #2: SERVER_IP

- Name: `SERVER_IP`
- Value: Your server IP (e.g., `203.0.113.42`)
- Click **"Add secret"**

### Secret #3: SERVER_USER

- Name: `SERVER_USER`
- Value: Your SSH username (e.g., `ubuntu`, `root`)
- Click **"Add secret"**

**Verify:** You should see 3 secrets in GitHub Settings

---

## ⚙️ Step 4: Server Setup (3 minutes)

**SSH to your server:**

```bash
ssh user@your-server-ip
```

**Create project directory:**

```bash
sudo mkdir -p /opt/rhd-estimation
sudo chown $USER:$USER /opt/rhd-estimation
```

**Clone repository:**

```bash
cd /opt/rhd-estimation
git clone https://github.com/YOUR_USERNAME/your-repo.git .
cd backend
```

**Create .env.prod:**

```bash
cp .env.prod.template .env.prod
nano .env.prod

# Required fields:
APP_ENV=production
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
DB_USER=rhd_estimation_user
DB_PASSWORD=<strong password>
DATABASE_URL=postgresql://...
```

**Create backups directory:**

```bash
mkdir -p /opt/rhd-estimation/backups
```

**Done!** Your server is ready.

---

## 🧪 Step 5: Test It (< 1 minute)

**Make a test change locally:**

```bash
# In your local repo
echo "# Test $(date)" >> backend/README.md
git add backend/README.md
git commit -m "test: trigger CI/CD"
git push origin main
```

**Watch it deploy:**

1. Go to GitHub → **Actions** tab
2. Click the running workflow
3. Watch it execute in real-time ✨

**Verify on server:**

```bash
# SSH to server
ssh user@your-server-ip

# Check if containers are running
cd /opt/rhd-estimation/backend
docker-compose -f docker-compose.prod.yml ps

# Check health
curl http://localhost:8000/health
```

**Result:**

```json
{
  "status": "healthy",
  "service": "estimation-backend"
}
```

---

## ✅ You're Done!

Your CI/CD pipeline is live! 🎉

---

## 📊 What Happens Now

Every time you push to `main` branch:

```
git push origin main
    ↓
GitHub Actions checks code
    ↓
Builds Docker image
    ↓
SSHs into your server
    ↓
Pulls latest code
    ↓
Deploys containers
    ↓
Runs health checks
    ↓
✅ Your changes are live (~11 minutes)
```

---

## 🔍 Monitor Deployments

### Check GitHub Actions

1. Go to your repository
2. Click **Actions** tab
3. See all workflow runs

### Check Server Logs

```bash
ssh user@your-server-ip
tail -f /opt/rhd-estimation/deployment.log
```

### Check Application Health

```bash
curl http://your-server-ip:8000/health
```

---

## 🎯 Next Steps

- [ ] Verify first deployment succeeded
- [ ] Test by making code changes and pushing
- [ ] (Optional) Add Slack notifications
- [ ] (Optional) Require approvals before deploy

---

## 📚 For More Details

- **Complete setup guide:** [CICD_SETUP.md](CICD_SETUP.md)
- **Architecture overview:** [CICD_ARCHITECTURE.md](CICD_ARCHITECTURE.md)
- **Workflow files:** [.github/workflows/](../.github/workflows/)

---

## 🆘 Quick Troubleshooting

| Problem                   | Quick Fix                                               |
| ------------------------- | ------------------------------------------------------- |
| "Permission denied"       | Verify SSH key on server (`cat ~/.ssh/authorized_keys`) |
| Deployment not triggering | Check: Does branch name match (main/master)?            |
| Health check fails        | Run: `docker-compose logs backend`                      |
| Git pull fails            | Verify: Git can pull on server: `git pull`              |

**More help:** See [CICD_SETUP.md](CICD_SETUP.md) troubleshooting section

---

**That's it! Your automated deployment is ready.** 🚀

Push code → GitHub Actions handles the rest → Your server updates automatically
