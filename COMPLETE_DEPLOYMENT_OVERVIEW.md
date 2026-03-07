# Complete Deployment Architecture Overview

**Purpose:** Understand your entire deployment system (Backend + Frontend)  
**Status:** 🎉 Ready to deploy!

---

## 🎯 Your Complete Application Stack

```
┌───────────────────────────────────────────────────────────────┐
│                    FRONTEND (Vercel)                          │
│                                                               │
│  • React/Vue/Svelte app                                      │
│  • User interface for estimation system                       │
│  • Makes API calls to backend                                │
│  • Hosted on global CDN (cloudflare/Vercel)                  │
│  • Auto-deploys on git push                                  │
│  • Cost: $0/month (free tier)                                │
│  • Domain: https://your-domain.vercel.app                    │
└───────────────┬─────────────────────────────────────────────┘
                │
                │ HTTPS API Calls
                │ GET /items, POST /projects, etc.
                │
┌───────────────▼─────────────────────────────────────────────┐
│                    BACKEND (Your Server)                     │
│                                                               │
│  ├─ FastAPI Framework                                        │
│  ├─ Running in Docker container                              │
│  ├─ Handles: Business logic, validation, API endpoints       │
│  ├─ Auto-deploys via GitHub Actions                          │
│  ├─ Cost: $5-20/month (your VPS)                             │
│  └─ Domain: https://api.your-domain.com (or your IP)         │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ PostgreSQL Database (Docker)                            │ │
│  │ ├─ All estimation data stored here                      │ │
│  │ ├─ Backed up before each deployment                     │ │
│  │ └─ On same server as backend                            │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Nginx (Reverse Proxy)                                   │ │
│  │ ├─ Handles HTTPS/SSL                                    │ │
│  │ ├─ Routes traffic to FastAPI                            │ │
│  │ └─ CORS headers configured                              │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Pipeline

### Frontend Deployment (Vercel)

```
Your Code: git push origin main/master
    ↓
    └→ GitHub webhook triggers Vercel
       ├─ Install dependencies (npm/yarn)
       ├─ Build the app (React/Vue/etc)
       ├─ Run tests (if configured)
       ├─ Deploy to global CDN
       └─ ~2-3 minutes: ✅ Live!
```

### Backend Deployment (GitHub Actions + Your Server)

```
Your Code: git push origin main/master
    ↓
    └→ GitHub Actions workflow triggered
       ├─ Test & Build Phase (on GitHub runner)
       │  ├─ Install Python dependencies
       │  ├─ Run syntax checks
       │  ├─ Run tests (if available)
       │  └─ Build Docker image
       │
       ├─ Deploy Phase (via SSH to your server)
       │  ├─ Connect securely with SSH key
       │  ├─ Pull latest code
       │  ├─ Build Docker image on server
       │  ├─ Back up database
       │  ├─ Stop old containers
       │  └─ Start new containers
       │
       └─ ~10-12 minutes: ✅ Live!
```

### Separate Repositories & Deployments

Your setup has **TWO separate GitHub repositories**:

```
GitHub
├─ frontend-repo/                    ← React/Vue app
│  └─ git push origin main
│     └─ Vercel auto-deploys (~3 min)
│
└─ backend-repo/                     ← FastAPI backend
   └─ git push origin main
      └─ GitHub Actions auto-deploys (~12 min)
```

**Deployment Timeline:**

```
Frontend Push:
  Time 0:00█ You: cd frontend-repo && git push origin main
  Time 0:05█ Vercel detects change
  Time 0:08█ Vercel builds React app
  Time 0:10█ ✅ Frontend LIVE (total: ~3 min)

Backend Push (separate):
  Time 0:00█ You: cd backend-repo && git push origin main
  Time 0:05█ GitHub Actions detects change
  Time 0:08█ Tests & builds Docker image
  Time 0:12█ SSH deploys to your server
  Time 0:15█ ✅ Backend LIVE (total: ~12 min)
```

**Key Point:** You need **two separate git pushes** (one in each repo), but both deploy automatically! ✅

---

## 🔐 Data Flow & Security

### HTTPS/SSL Everywhere

```
User's Browser
    ↓ (HTTPS)
Vercel CDN
    ↓ (Your domain)
    └→ Your Frontend App (React/Vue)
       ↓ (HTTPS API calls)
       └→ Your Backend (FastAPI)
          ↓ (Internal Docker network)
          └→ PostgreSQL Database
```

**Security Features:**

- ✅ All connections encrypted (HTTPS/TLS)
- ✅ SSL certificates auto-generated (Vercel + Nginx)
- ✅ CORS properly configured
- ✅ Database only accessible from backend
- ✅ SSH key authentication for CI/CD
- ✅ Environment secrets encrypted
- ✅ No credentials in code

---

## 💾 Data & Backups

### Where Your Data Lives

```
Vercel (Stateless - NO data stored)
├─ Just serves frontend files
└─ No persistent data

Your Server (Stateful - ALL data stored)
├─ PostgreSQL: Stores all estimations
├─ Backups: Created before each deployment
└─ Logs: Stored for monitoring
```

### Backup Strategy

```
Every deployment:
    ├─ Before stopping containers
    ├─ Run: pg_dump (database backup)
    ├─ Save to: /opt/rhd-estimation/backups/
    └─ Keep last 30 days worth
       └─ Can restore if something goes wrong
```

---

## 📊 Estimated Costs

### Monthly Costs

| Component        | Cost            | Details                             |
| ---------------- | --------------- | ----------------------------------- |
| **Frontend**     | $0              | Vercel free tier (100GB bandwidth)  |
| **Backend & DB** | $5-20           | Shared server (depends on provider) |
| **Domain Names** | $0-15           | Optional custom domain              |
| **SSL/TLS**      | $0              | Auto-generated (included)           |
| **Total**        | **$5-20/month** | Professional hosting!               |

### Why This is Cheap

- **Vercel handlesscaling** - No need for load balancers
- **Your server is shared** - Not dedicated (shared cloud server)
- **No database licensing** - PostgreSQL is free
- **No CI/CD licensing** - GitHub Actions is free
- **Everything automated** - No manual DevOps costs

**Comparison:**

- AWS Elastic Beanstalk: $30-100+/month
- Heroku: $50-500+/month
- DigitalOcean Managed App Platform: $30-100+/month
- **Your Setup: $5-20/month** ✅

---

## 🔄 Development Workflow

### Day-to-Day Development (Two Separate Repos)

**For Frontend Changes:**

```
1. Navigate to frontend repo
   cd ~/your-frontend-repo

2. Create feature branch
   git checkout -b feature/my-feature

3. Make changes to React/Vue code
   code src/components/...

4. Test locally
   npm run dev

5. Commit & push
   git add .
   git commit -m "feat: new UI"
   git push origin feature/my-feature

6. Create Pull Request
   GitHub → Create PR → Review → Merge

7. Merged! Vercel automatically deploys
   └─ Vercel detects merge to main
   └─ Builds & deploys in ~3 minutes
   └─ Check: Vercel Dashboard
```

**For Backend Changes:**

```
1. Navigate to backend repo
   cd ~/your-backend-repo

2. Create feature branch
   git checkout -b feature/my-feature

3. Make changes to FastAPI code
   code app/routers/...

4. Test locally
   docker-compose up

5. Commit & push
   git add .
   git commit -m "feat: new API endpoint"
   git push origin feature/my-feature

6. Create Pull Request
   GitHub → Create PR → Review → Merge

7. Merged! GitHub Actions automatically deploys
   └─ GitHub Actions detects merge to main
   └─ Tests, builds, deploys in ~12 minutes
   └─ Check: GitHub Actions tab
```

**Both update independently!**

```
Frontend Repo: git push → Vercel deploys
Backend Repo:  git push → GitHub Actions deploys

No coordination needed - they work separately!
```

### No More Manual Work! ✨

**Before CI/CD:**

```
1. SSH to server
2. git pull
3. docker-compose build
4. docker-compose down
5. docker-compose up -d
6. Check if working...
7. Pray nothing broke
```

**With CI/CD:**

```
1. git push
2. ✓ Done! Automatic!
```

---

## 🎯 Environment Configuration

### Frontend (.env.production on Vercel)

```
# In Vercel dashboard, set environment variables:
VITE_API_URL=https://api.your-domain.com

# In your React code:
const API_URL = import.meta.env.VITE_API_URL;
fetch(`${API_URL}/items`)
```

### Backend (.env.prod on your server)

```
# In /opt/rhd-estimation/backend/.env.prod:
APP_ENV=production
SECRET_KEY=<your-secret>
DATABASE_URL=postgresql://user:password@db:5432/rhd_estimation
CORS_ORIGINS=https://your-domain.vercel.app
```

### GitHub Secrets (for CI/CD)

```
# GitHub Settings → Secrets → Actions:
SSH_PRIVATE_KEY=<your-ssh-key>
SERVER_IP=<your-server-ip>
SERVER_USER=<your-ssh-username>
```

---

## 🔍 Monitoring & Troubleshooting

### Frontend Monitoring (Vercel)

```
Vercel Dashboard:
├─ Deployments tab → See all history
├─ Builds take 2-3 minutes
├─ Failed? Click deployment to see logs
└─ Analytics tab → See traffic, errors

GitHub Actions:
├─ Actions tab → See build status
└─ Click deployment for real-time logs
```

### Backend Monitoring (Your Server)

```
GitHub Actions:
├─ Actions tab → Deployment status
└─ Click "Deploy" job for detailed logs

Server Logs:
├─ SSH to server
├─ tail -f /opt/rhd-estimation/deployment.log
└─ Watch deployment in real-time

Docker Logs:
├─ docker-compose -f docker-compose.prod.yml logs -f
├─ Shows container output
└─ Useful for debugging

Health Check:
├─ curl https://api.your-domain.com/health
├─ Should return: {"status":"healthy"}
└─ This is your liveliness check
```

### When Something Goes Wrong

```
Step 1: Check GitHub Actions logs (most detailed)
Step 2: Check server deployment log
Step 3: Check Docker container logs
Step 4: SSH to server and inspect

If deployphant fails:
├─ Database backup exists
├─ Previous containers still running
└─ Can rollback: git reset --hard previous-commit
```

---

## 📈 Scaling Strategy

### If Traffic Increases

**Front-end:** Vercel automatically scales ✅

- Handles millions of requests
- Already on global CDN
- No configuration needed

**Backend:** Upgrade server if needed

```
Single thread:
├─ ~100 concurrent users per 1GB RAM
├─ Your $5-20 server: 1-2GB RAM
└─ Capacity: 100-200 concurrent users

If you need more:
├─ Upgrade to larger server (+25-50/month)
├─ Or add load balancer
└─ Docker makes this easy
```

**Database:** PostgreSQL is powerful

```
Single instance handles:
├─ Millions of records
├─ Thousands of queries/second
└─ Add replication only if massive scale needed
```

---

## 🔄 Backup & Recovery

### Database Backups

```
Automatic (before each deploy):
├─ Location: /opt/rhd-estimation/backups/
├─ Format: SQL dump files
├─ Kept: Last 30 days
└─ Size: Varies by data size

Manual backup:
docker-compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U rhd_estimation_user rhd_estimation > backup.sql

Restore:
docker-compose -f docker-compose.prod.yml exec -T db \
  psql -U rhd_estimation_user rhd_estimation < backup.sql
```

### Code Rollback

```
If you deploy bad code:
├─ Go to GitHub
├─ Revert commit
├─ Push new commit
├─ Both Vercel and GitHub Actions auto-deploy ✓

Or manual:
ssh user@your-server-ip
cd /opt/rhd-estimation/backend
git reset --hard previous-commit
docker-compose -f docker-compose.prod.yml restart
```

---

## ✨ Best Practices

### DO ✅

✅ Use both Vercel (free frontend) and your server (backend)  
✅ Keep database on your server (you control data)  
✅ Use environment variables for configuration  
✅ Monitor deployments after each push  
✅ Keep database backups  
✅ Test locally before pushing  
✅ Use feature branches for development  
✅ Review code in PRs before merging

### DON'T ❌

❌ Don't use Vercel as a database (it's stateless)  
❌ Don't commit .env files (already in .gitignore!)  
❌ Don't run backend-only code on Vercel  
❌ Don't skip security scans  
❌ Don't blindly merge without testing  
❌ Don't store secrets in code

---

## 🎓 Key Concepts

### Vercel (Frontend)

**What it is:** Serverless platform for modern frontends  
**Best for:** React, Vue, Next.js, etc.  
**Why:**

- Automatic CDN everywhere
- Build optimization
- Previews for every PR
- Zero configuration

### Your Server (Backend)

**What it is:** Your own Docker-powered server  
**What runs:** FastAPI, PostgreSQL, Nginx  
**Why:**

- Full control over data
- Runs long-lived processes
- Manages database
- More secure (controls access)

### GitHub Actions (CI/CD)

**What it is:** Automation platform from GitHub  
**What it does:**

- Runs tests on every commit
- Builds Docker images
- Deploys to your server
- Sends notifications

### Docker (Containerization)

**What it is:** Container engine  
**What it provides:**

- Same environment dev = prod
- Easy scaling
- Isolated services (DB, API, Nginx)
- Version control for infrastructure

---

## 📚 Quick Reference

### When You Push Code (Separate Repos = Two Pushes)

**Push #1 - Frontend:**

```
cd ~/frontend-repo
git push origin main
    ↓
Vercel webhook triggered
├─ npm install
├─ npm run build
├─ Run tests
├─ Deploy to CDN
└─ ~3 minutes: ✅ Live!
```

**Push #2 - Backend:**

```
cd ~/backend-repo
git push origin main
    ↓
GitHub Actions workflow triggered
├─ Install Python deps
├─ Run tests/checks
├─ Build Docker image
├─ SSH to your server
├─ docker-compose up -d
└─ ~12 minutes: ✅ Live!
```

**Both run independently** - no waiting for each other!

### To Monitor

```
Frontend: Vercel Dashboard or GitHub Actions
Backend: GitHub Actions logs or tail -f on server
Database: Check backups in /opt/rhd-estimation/backups/
Health: curl https://api.your-domain.com/health
```

### To Rollback

```
Frontend: Revert commit → Vercel automatically redeploys
Backend: Revert commit → GitHub Actions automatically redeploys
Database: Restore from backup in /opt/rhd-estimation/backups/
```

---

## 🎉 Summary

**You now have:**

✅ Professional, scalable architecture  
✅ Automatic deployments for both frontend and backend  
✅ Global CDN for frontend (Vercel)  
✅ Secure backend on your server  
✅ Database backups  
✅ Health monitoring  
✅ Security best practices  
✅ Cost-effective ($5-20/month)

**All with just a `git push`!** 🚀

---

## 📊 Deployment Checklist (Final)

- [ ] Backend deployed to your server ✅
- [ ] Containers running and healthy ✅
- [ ] GitHub Actions CI/CD working ✅
- [ ] Database backups automated ✅
- [ ] Frontend ready for Vercel (React/Vue built)
- [ ] Vercel account created
- [ ] Frontend repository connected to Vercel
- [ ] Frontend environment variables set (API_URL)
- [ ] Both deploy automatically on git push
- [ ] Monitoring set up (logs, health checks)
- [ ] Team knows deployment process
- [ ] Backups tested and documented

---

**Everything is ready. Just push code and watch both frontend and backend deploy automatically!** 🎉
