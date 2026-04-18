# SportIQ — Deployment Guide

## Overview

- **Frontend** → Vercel (free tier, static hosting)
- **Backend** → Render (free tier, Python web service)

---

## 1. Backend Deployment (Render)

### Prerequisites
- Push code to GitHub
- Create a free [Render](https://render.com) account

### Steps

1. **Log in** to [Render Dashboard](https://dashboard.render.com)

2. **Create New Web Service:**
   - Click **"New +"** → **"Web Service"**
   - Connect your GitHub repository

3. **Configure:**
   | Setting | Value |
   |---------|-------|
   | **Name** | `sportiq-backend` |
   | **Runtime** | Python 3 |
   | **Root Directory** | (leave empty — root of repo) |
   | **Build Command** | `pip install -r backend/requirements.txt` |
   | **Start Command** | `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | Free |

4. **Deploy** — click "Create Web Service"

5. **Get your URL:** `https://sportiq-backend.onrender.com`

### Important Notes

> ⚠️ **Cold Starts:** Free tier sleeps after 15 min of inactivity. First request takes 30-60 seconds.

> ⚠️ **No Persistent Storage:** Processed videos are lost on restart. They are served immediately after processing.

> ⚠️ **Resource Limits:** Free tier has limited CPU/RAM. Keep demo videos under 30 seconds.

---

## 2. Frontend Deployment (Vercel)

### Prerequisites
- Push code to GitHub
- Create a free [Vercel](https://vercel.com) account

### Steps

1. **Log in** to [Vercel Dashboard](https://vercel.com/dashboard)

2. **Import Project:**
   - Click **"Add New..."** → **"Project"**
   - Connect GitHub and select your repo

3. **Configure:**
   | Setting | Value |
   |---------|-------|
   | **Framework Preset** | Other |
   | **Root Directory** | `frontend` |
   | **Build Command** | (leave empty — static site) |
   | **Output Directory** | `.` |

4. **Deploy** — click "Deploy"

5. **Get your URL:** `https://sportiq.vercel.app`

### Update Backend URL

After deploying the backend, update the API URL in `frontend/js/app.js`:

```javascript
const CONFIG = {
  API_BASE_URL: 'https://sportiq-backend.onrender.com',
  // ...
};
```

Then push the change — Vercel will auto-redeploy.

---

## 3. Local Development

### Backend
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Start server with hot reload
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
# Option 1: Open directly in browser
start frontend/index.html  # Windows

# Option 2: Use VS Code Live Server extension
# Right-click index.html → "Open with Live Server"

# Option 3: Python HTTP server
cd frontend
python -m http.server 3000
```

---

## 4. Verification Checklist

After deployment, verify:

- [ ] Backend health: `GET https://your-backend.onrender.com/health`
- [ ] API docs load: `https://your-backend.onrender.com/docs`
- [ ] Frontend loads at Vercel URL
- [ ] Upload a test video → get processed result
- [ ] Side-by-side video display works
- [ ] Stats display correctly
