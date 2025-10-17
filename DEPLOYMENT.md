# Deployment Guide

## 🚀 Vercel Deployment (Frontend)

### 1. Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click "New Project"
3. Import your GitHub repository
4. Vercel will auto-detect Next.js and configure build settings

### 2. Environment Variables

Add these environment variables in Vercel dashboard:

```
NEXT_PUBLIC_API_BASE_URL=https://ai-fantasy-football.onrender.com
```

Or if your backend is deployed elsewhere, use that URL.

### 3. Build Settings (Should be auto-configured)

- **Framework Preset:** Next.js
- **Build Command:** `cd frontend && npm run build`
- **Output Directory:** `frontend/.next`
- **Install Command:** `cd frontend && npm install`

## 🐍 Backend Deployment

Your Python FastAPI backend is currently running on:
- **Production:** https://ai-fantasy-football.onrender.com
- **Local:** http://localhost:8000

Make sure your backend is deployed and accessible at the URL you set in `NEXT_PUBLIC_API_BASE_URL`.

## 📁 Project Structure

```
your-repo/
├── frontend/          # Next.js app (deploys to Vercel)
├── api/              # Python FastAPI backend
├── vercel.json       # Vercel configuration
└── DEPLOYMENT.md     # This file
```

## 🔗 URLs After Deployment

- **Frontend:** https://your-app.vercel.app
- **Backend:** https://ai-fantasy-football.onrender.com (already deployed)

## 🛠 Development vs Production

- **Local Development:** Frontend calls `http://localhost:8000`
- **Production:** Frontend calls `https://ai-fantasy-football.onrender.com`
