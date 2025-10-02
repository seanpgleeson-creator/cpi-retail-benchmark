# Deployment Guide: GitHub + Vercel

This guide walks through deploying the CPI Retail Benchmark Platform using GitHub and Vercel.

## Prerequisites

- [x] Local repository setup complete
- [x] All code committed to git
- [ ] GitHub account
- [ ] Vercel account (free tier available)

## Step 1: Create GitHub Repository

1. **Go to [GitHub.com](https://github.com)** and sign in
2. **Click "New repository"** (green button or + icon)
3. **Configure repository:**
   ```
   Repository name: cpi-retail-benchmark
   Description: Multi-Retailer CPI Price Benchmark Platform - Real-time retail price tracking vs government inflation data
   Visibility: Public ✅
   Initialize with:
   - README: ❌ (we already have one)
   - .gitignore: ❌ (we already have one)
   - License: ❌ (we already have one)
   ```
4. **Click "Create repository"**

## Step 2: Push Local Code to GitHub

After creating the repository, run these commands in your terminal:

```bash
# Add GitHub as remote origin (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/cpi-retail-benchmark.git

# Ensure we're on main branch
git branch -M main

# Push code to GitHub
git push -u origin main
```

**Expected output:**
```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
Delta compression using up to X threads
Compressing objects: 100% (X/X), done.
Writing objects: 100% (X/X), X.XX KiB | X.XX MiB/s, done.
Total X (delta X), reused 0 (delta 0), pack-reused 0
To https://github.com/YOUR_USERNAME/cpi-retail-benchmark.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

## Step 3: Connect to Vercel

1. **Go to [Vercel.com](https://vercel.com)** and sign up/sign in
2. **Click "New Project"**
3. **Import Git Repository:**
   - Select "Import Git Repository"
   - Choose your GitHub account
   - Find and select `cpi-retail-benchmark`
   - Click "Import"

## Step 4: Configure Vercel Project Settings

### Framework Preset
- **Framework Preset**: Other
- **Build Command**: `pip install -r requirements.txt`
- **Output Directory**: Leave empty
- **Install Command**: `pip install -r requirements.txt`

### Environment Variables

Add these environment variables in Vercel dashboard:

#### Required Variables:
```bash
# BLS API (optional but recommended)
BLS_API_KEY=your_bls_api_key_here

# Database (Vercel will provide PostgreSQL)
DATABASE_URL=postgresql://...

# Application Settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key

# CORS Origins (add your Vercel domain)
CORS_ORIGINS=https://your-app.vercel.app,https://cpi-retail-benchmark.vercel.app
```

#### Optional Variables:
```bash
# Scraping Configuration
ZIP_CODE=55331
HEADLESS=true
SCRAPE_MAX_PAGES=5
SCRAPE_DELAY_RANGE_MS=1000-3000

# Rate Limiting
API_RATE_LIMIT=100
API_RATE_LIMIT_WINDOW=3600

# Logging
LOG_LEVEL=INFO
```

## Step 5: Deploy

1. **Click "Deploy"** in Vercel
2. **Wait for build** (first deployment takes 2-5 minutes)
3. **Visit your deployed app** at the provided URL

## Step 6: Configure Automatic Deployments

### Branch Configuration:
- **Production Branch**: `main` (auto-deploys to production)
- **Preview Branches**: All other branches (creates preview deployments)

### GitHub Integration:
- **Pull Request Previews**: ✅ Enabled
- **Automatic Deployments**: ✅ Enabled
- **Build Logs**: ✅ Public

## Step 7: Custom Domain (Optional)

1. **Go to Project Settings** → **Domains**
2. **Add your custom domain**
3. **Configure DNS** as instructed by Vercel
4. **Update CORS_ORIGINS** environment variable

## Verification Checklist

After deployment, verify:

- [ ] **Homepage loads** without errors
- [ ] **API endpoints** respond (check `/docs` for FastAPI)
- [ ] **Environment variables** are loaded correctly
- [ ] **Database connection** works (if configured)
- [ ] **GitHub Actions** run successfully on push
- [ ] **Preview deployments** work for PRs

## Troubleshooting

### Common Issues:

1. **Build Fails**:
   - Check build logs in Vercel dashboard
   - Verify all dependencies in requirements.txt
   - Check Python version compatibility

2. **Environment Variables**:
   - Ensure all required variables are set
   - Check for typos in variable names
   - Verify values don't contain special characters

3. **Database Connection**:
   - Verify DATABASE_URL format
   - Check database provider settings
   - Ensure database is accessible from Vercel

### Getting Help:

- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **GitHub Actions Logs**: Check repository Actions tab
- **Project Issues**: Create issue in GitHub repository

## Next Steps

After successful deployment:

1. **Set up monitoring** (Vercel Analytics)
2. **Configure alerts** for deployment failures
3. **Set up staging environment** (optional)
4. **Add custom domain** (optional)
5. **Configure database backups**

---

**🎉 Congratulations!** Your CPI Retail Benchmark Platform is now deployed and ready for development!
