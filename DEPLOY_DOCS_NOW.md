# Quick Deployment Guide - Read the Docs

## Deploy Your Documentation in 5 Minutes

Your RadiKal V2.0 documentation is ready to deploy to Read the Docs for FREE!

### Prerequisites

- GitHub account
- Your code pushed to GitHub

### Step 1: Push to GitHub (if not already done)

```bash
# Add all documentation files
git add .readthedocs.yaml mkdocs.yml docs/

# Commit
git commit -m "Add Read the Docs documentation"

# Push to GitHub
git push origin main
```

### Step 2: Deploy to Read the Docs

1. Go to https://readthedocs.org

2. Click **"Sign Up"** or **"Log In"** (use GitHub login)
   - Click "Sign in with GitHub"
   - Authorize Read the Docs

3. Click **"Import a Project"**
   - You'll see your GitHub repositories
   - Find and select **"RadiKal-V2.0"**
   - Click **"+"** next to it

4. Configure Project (usually auto-detected):
   - **Name**: RadiKal-V2.0
   - **Repository URL**: (auto-filled)
   - **Default branch**: main
   - Click **"Next"**

5. Wait for Build (~2 minutes)
   - Read the Docs will automatically:
     - Detect `.readthedocs.yaml`
     - Install dependencies from `docs/requirements.txt`
     - Build with MkDocs
     - Deploy to their CDN

6. Your Documentation is Live!
   - URL will be: `https://radikal-v2.readthedocs.io`
   - Or: `https://radikal-v2.readthedocs.io/en/latest/`

### Step 3: Custom Domain (Optional)

If you have a domain, you can add:
- Go to project settings
- Click "Domains"
- Add your custom domain

### That's It!

Your documentation is now:
- Live and accessible worldwide
- Automatically rebuilds on every git push
- Free forever for open source projects
- Has search functionality
- Mobile responsive

---

## Verify Deployment

After deployment, visit your documentation and check:

- [ ] Home page loads: https://radikal-v2.readthedocs.io
- [ ] Navigation works
- [ ] Search works (top right)
- [ ] All pages accessible
- [ ] Links work
- [ ] Dark/light mode toggle works

---

## Auto-Update on Push

Every time you push changes to GitHub:
1. Read the Docs detects the push (webhook)
2. Automatically rebuilds documentation
3. Updates live site within 2-3 minutes

No manual deployment needed!

---

## Troubleshooting

### Build Failed

1. Check build logs on Read the Docs
2. Verify `.readthedocs.yaml` is in root directory
3. Verify `mkdocs.yml` is in root directory
4. Check `docs/requirements.txt` exists

### Documentation Not Updating

1. Check if webhook is enabled:
   - Project Settings → Integrations
   - Should see GitHub webhook
2. Manually trigger build:
   - Go to "Builds" tab
   - Click "Build Version"

---

## What You Get for Free

- Unlimited documentation hosting
- Automatic HTTPS
- Global CDN (fast worldwide)
- Version management (multiple versions)
- PDF/EPUB/HTML exports
- Search functionality
- Analytics
- Custom domains support
- 99.9% uptime SLA

**Cost: $0 forever** (for open source projects)

---

## Next Steps

Once documentation is deployed:

1. Share the link: `https://radikal-v2.readthedocs.io`
2. Add badge to your README:
   ```markdown
   [![Documentation Status](https://readthedocs.org/projects/radikal-v2/badge/?version=latest)](https://radikal-v2.readthedocs.io/en/latest/?badge=latest)
   ```
3. Consider deploying frontend/backend (see FREE_DEPLOYMENT_GUIDE.md)

---

**Your documentation is production-ready and waiting to be deployed!**

Just follow the 3 steps above and you'll have a professional documentation website live in 5 minutes.
