# 🏏 SportIQ — AI-Powered Cricket Performance Analyzer

<div align="center">

![SportIQ](frontend/assets/logo.png)

**Upload a cricket video → AI detects body pose → Display skeleton output**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)

[Live Demo](#) · [API Docs](#) · [Report Bug](../../issues) · [Request Feature](../../issues)

</div>

---

## 📋 About The Project

**SportIQ** is a web application that uses AI-powered computer vision to analyze cricket batting technique. Users upload a cricket video, and the system automatically:

1. **Detects body pose** using Google's MediaPipe (33 body landmarks)
2. **Draws a skeleton overlay** with cricket-specific color coding
3. **Extracts keypoint data** as structured JSON for analysis
4. **Calculates joint angles** for technique assessment

> *"I built a web app where a user uploads a cricket video and the AI automatically detects and draws the player body pose on the video. This is the computer vision foundation on which shot comparison, coaching feedback, and the coach dashboard will be built next semester."*

### Built With

| Component | Technology |
|-----------|-----------|
| AI / ML | Python, MediaPipe, OpenCV, NumPy |
| Backend | FastAPI, Uvicorn |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Deployment | Render (Backend), Vercel (Frontend) |

---

## 🏗️ Architecture

```
┌──────────────┐     POST /api/v1/upload     ┌──────────────────┐
│              │ ──────────────────────────►  │                  │
│   Frontend   │                              │  FastAPI Backend  │
│   (Vercel)   │  ◄────────────────────────── │    (Render)      │
│              │   JSON + Video URL           │                  │
└──────────────┘                              └────────┬─────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │   ML Pipeline     │
                                              │  ┌──────────────┐ │
                                              │  │  MediaPipe    │ │
                                              │  │  Pose         │ │
                                              │  └──────┬───────┘ │
                                              │         ▼         │
                                              │  ┌──────────────┐ │
                                              │  │  Skeleton     │ │
                                              │  │  Drawer       │ │
                                              │  └──────┬───────┘ │
                                              │         ▼         │
                                              │  ┌──────────────┐ │
                                              │  │  Keypoint     │ │
                                              │  │  Extractor    │ │
                                              │  └──────────────┘ │
                                              └──────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+** installed
- **pip** package manager
- A modern web browser

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/SmartCoachAI.git
   cd SmartCoachAI
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Start the backend server**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Open the frontend**
   - Open `frontend/index.html` in your browser
   - Or use a live server extension

6. **Upload a cricket video and see the magic! 🏏**

---

## 📁 Project Structure

```
SmartCoachAI/
├── frontend/                    # Frontend Lead
│   ├── index.html               # Main page
│   ├── css/style.css            # Premium dark theme
│   ├── js/app.js                # Upload logic & API calls
│   ├── assets/                  # Logo & hero images
│   └── vercel.json              # Vercel deployment
│
├── backend/                     # Backend Lead
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Configuration
│   ├── routers/video.py         # API endpoints
│   ├── services/pose_service.py # ML integration service
│   ├── requirements.txt         # Python dependencies
│   └── Procfile                 # Render deployment
│
├── ml/                          # AI/ML Lead
│   ├── pose_estimator.py        # Core pose estimation pipeline
│   ├── skeleton_drawer.py       # Skeleton visualization
│   ├── keypoint_extractor.py    # Keypoint JSON export
│   ├── angle_calculator.py      # Joint angle math
│   └── utils.py                 # Video I/O utilities
│
├── docs/                        # DevOps + Docs
│   ├── architecture.md          # Architecture diagram
│   ├── api_docs.md              # API documentation
│   └── deployment_guide.md      # Deployment guide
│
├── .gitignore
├── README.md
└── LICENSE
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/status` | API status & capabilities |
| `POST` | `/api/v1/upload` | Upload video for processing |
| `GET` | `/api/v1/video/{filename}` | Get processed video |
| `GET` | `/api/v1/keypoints/{filename}` | Get keypoints JSON |

### Upload Example

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@cricket_video.mp4" \
  -F "sport=cricket" \
  -F "shot_type=cover_drive"
```

### Response

```json
{
  "status": "success",
  "data": {
    "video_url": "/api/v1/video/pose_cricket_video.mp4",
    "keypoints_url": "/api/v1/keypoints/keypoints_cricket_video.json",
    "stats": {
      "total_frames": 150,
      "frames_with_pose": 142,
      "detection_rate_percent": 94.7,
      "processing_time_seconds": 12.5
    }
  }
}
```

---

## 🔮 Roadmap

### This Semester ✅
- [x] Video upload through webpage
- [x] AI pose estimation with skeleton overlay
- [x] Processed video display with stats

### Next Semester 🚧
- [ ] Shot comparison engine (user vs. reference)
- [ ] Feedback generator (human-readable technique advice)
- [ ] Scoring system (0–100 per shot type)
- [ ] Injury risk detection (dangerous joint angles)
- [ ] Coach dashboard (view all player performances)
- [ ] Playing 11 selector (AI-based team selection)
- [ ] Football support

---

## 👥 Team

| Role | Name | Branch |
|------|------|--------|
| 🧠 AI / ML Lead | Person 1 | `feature/p1-mediapipe` |
| ⚙️ Backend Lead | Person 2 | `feature/p2-backend` |
| 🎨 Frontend Lead | Person 3 | `feature/p3-frontend` |
| 🔧 DevOps + Docs | Person 4 | `feature/p4-devops` |

---

## 🌐 Live Links

| Service | URL |
|---------|-----|
| Frontend | [sportiq.vercel.app](#) |
| Backend API | [sportiq-backend.onrender.com](#) |
| API Docs | [sportiq-backend.onrender.com/docs](#) |

---

## 📝 License

This project is licensed under the MIT License.

---

<div align="center">

**🏏 SportIQ — Built by 4 students, solving a real problem.**

*College Mega Project — Semester 1*

</div>
