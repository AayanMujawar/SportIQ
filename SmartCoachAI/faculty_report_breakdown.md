# 🎓 SportIQ SmartCoachAI: Faculty Presentation Guide & Technical Breakdown

This document provides a highly detailed, professional analysis of the **SportIQ SmartCoachAI** codebase. It is designed to help you confidently present the technical implementation, software architecture, and machine learning pipelines to your college faculty.

---

## 1. Project Architecture & Technical Stack

The system employs a modern **Three-Tier Architecture**, decoupling the interface, server logic, and machine learning engine to ensure high scalability and modularity.

*   **Tier 1: Client/Frontend Layer (Vercel)**
    *   **Technologies:** HTML5, Vanilla CSS3, Vanilla JavaScript. No heavy frameworks (like React) were used to demonstrate core DOM manipulation and fetch API competency.
*   **Tier 2: Backend REST API Layer (Render)**
    *   **Technologies:** Python 3.9, FastAPI, Uvicorn. Selected for its asynchronous capabilities and automatic OpenAPI (Swagger) documentation generation.
*   **Tier 3: Machine Learning Engine**
    *   **Technologies:** Google MediaPipe (Pose solution), OpenCV (`cv2`), NumPy. This layer runs within the backend environment but maintains its own abstraction via strict service boundaries.

---

## 2. Frontend Layer Breakdown

The frontend manages user interactions and HTTP handshakes with the server.

### `frontend/index.html`
*   **Role:** The semantic structural foundation.
*   **Technical Details:** 
    *   Contains the application's meta tags for Search Engine Optimization (SEO).
    *   Implements a clean UI broken down into `hero`, `upload`, `processing-section`, and `results-section` divisions.
    *   Utilizes HTML5 `<video>` tags dynamically controlled via JavaScript to display side-by-side original and skeletal views.

### `frontend/css/style.css`
*   **Role:** The styling engine.
*   **Technical Details:** 
    *   Employs **CSS Variables** (Custom Properties) to maintain a consistent "Dark Mode / Glassmorphism" theme. 
    *   Utilizes CSS Grid and Flexbox for responsive design.
    *   Implements complex CSS keyframe animations (like `pulse-dot`) directly in the stylesheet rather than relying on heavy JS libraries.

### `frontend/js/app.js`
*   **Role:** The dynamic application state controller.
*   **Technical Details:**
    *   **Event Delegation:** Listens for Drag & Drop events via the `dragover` and `drop` DOM events, giving the user a robust file-upload experience.
    *   **Asynchronous Comm:** Uses the modern `async/await` syntax alongside the built-in `fetch()` API to construct a `FormData` payload containing the compressed video, which is securely transmitted to `/api/v1/upload`.
    *   **UX Simulation:** To keep users engaged during heavy ML processing, `app.js` runs a simulated progress interval, displaying phases like "Initializing MediaPipe" before the server responds.
    *   **Dynamic Data Binding:** Extracts `stats` (FPS, detection percentages) from the server's JSON response and binds them to the DOM dynamically using easing-curve counter animations.

---

## 3. Backend API Layer Breakdown

The FastAPI server safely controls the data flow between the user and the ML models.

### `backend/main.py`
*   **Role:** The application bootstrap file.
*   **Technical Details:**
    *   Instantiates the `FastAPI` app.
    *   Attaches `CORSMiddleware` which is essential for cross-origin requests (Browser requesting from Vercel to a server on Render).
    *   Hooks into `@app.on_event("startup")` and `"shutdown"` to safely allocate and garbage-collect temp directories, ensuring the server doesn't hit Disk Space limits on Render servers over time.

### `backend/config.py`
*   **Role:** Centralized configuration matrix.
*   **Technical Details:**
    *   Implements "Separation of Concerns" by storing constants like `MAX_FILE_SIZE_MB`, file MIME validation arrays, and MediaPipe confidence thresholds (`MIN_DETECTION_CONFIDENCE = 0.5`) in a single observable file.

### `backend/routers/video.py`
*   **Role:** The HTTP Endpoint Router.
*   **Technical Details:**
    *   **Endpoint `/upload`:** Uses FastAPI's `UploadFile` class to stream the video chunk-by-chunk onto the server disk (`await file.read(1024 * 1024)`). *This is crucial to explain to faculty: streaming the file prevents the backend from crashing due to RAM exhaustion on large files.*
    *   Invokes the `PoseService` synchronously (as ML tasks are CPU bound, async wouldn't help standard ML without celery/workers), retrieves the generated file paths, and constructs the JSON response.
    *   **Endpoints `/video/{filename}` & `/keypoints/{filename}`:** Utilizes `FileResponse` objects to safely serve artifacts back to the browser.

### `backend/services/pose_service.py`
*   **Role:** The Abstraction/Service boundary.
*   **Technical Details:**
    *   Ensures that HTTP logic (`video.py`) doesn't directly touch ML logic (`pose_estimator.py`). It sanitizes file paths, gauges total `start_time` / `end_time` execution metrics for logging, and handles exception catching (returning proper Http-500 codes if the ML fails).

---

## 4. Machine Learning & Computer Vision Breakdown

This is the core academic substance of the project.

### `ml/pose_estimator.py`
*   **Role:** The Computer Vision Orchestrator.
*   **Technical Details:**
    *   Uses OpenCV `cv2.VideoCapture` to load the video frame matrix.
    *   Instantiates Google's `mp.solutions.pose.Pose` module. 
    *   **Crucial Step:** Iterates `while True: cap.read()`. It must convert raw frames from BGR (OpenCV's default) to RGB (MediaPipe's requirement) before passing them to the neural network.
    *   If `results.pose_landmarks` mathematically intersect, it fires the `SkeletonDrawer` and `KeypointExtractor`, then pushes the modified frame array into `cv2.VideoWriter`.

### `ml/skeleton_drawer.py`
*   **Role:** Visualization logic for the body overlay.
*   **Technical Details:**
    *   Groups human anatomy into arrays (`UPPER_LANDMARKS`, `LOWER_LANDMARKS`).
    *   Iterates through `mp_pose.POSE_CONNECTIONS` tracing lines (`cv2.line`) and node circles (`cv2.circle`) strictly over points that surpass a `.visibility` float of `0.5`, ensuring the system doesn't draw broken arms when joints are occluded.
    *   Applies Alpha Blending (`cv2.addWeighted`) to create a slightly transparent, aesthetically pleasing glow over the original footage.

### `ml/angle_calculator.py`
*   **Role:** Biomechanical mathematics engine.
*   **Technical Details:**
    *   Converts visual data into physical physics. It expects 3 cartesian keypoints (x, y). 
    *   Uses **Dot Product Vector Mathematics**: It calculates the vector vectors from the vertex (`va`, `vb`), measures the dot product divided by the normalized magnitudes, and computes the `arccos` to extract precise internal joint angles (Degrees). This proves your application not only traces images but applies pure mathematics to them.

### `ml/keypoint_extractor.py`
*   **Role:** Data Serialization.
*   **Technical Details:**
    *   Takes transient neural network data in RAM and formats it into persistent, deeply nested JSON lists. This creates a data pipeline where a single video upload yields structured numerical data that could be used in future semesters for Neural Network training or purely programmatic grading.

### `ml/utils.py`
*   **Role:** CV2 Helper logic.
*   **Technical Details:**
    *   Calculates FPS ratios and provides the `resize_frame` logic. To guarantee the pose model doesn't bog down, it algorithmically calculates scalar down-scaling to ensure no frame is larger than 720p before ML processing begins.

---

## 💡 Top Discussion Points for Faculty Q&A:
1.  **Memory Management:** Address how `video.py` streams user uploads in chunks instead of loading entire videos into RAM.
2.  **Algorithm Efficiency:** Explain that `utils.py` dynamically resizes frames to `1280x720` to prevent Google MediaPipe from over-processing 4k videos, ensuring rapid responses.
3.  **Modular Abstraction:** Showcase how `pose_service.py` completely isolates the HTTP APIs from the ML logic, allowing either side to be scaled or replaced independently.
4.  **Math Application:** Highlight `angle_calculator.py` to prove that you utilized complex vector math (Dot products & Arccosine) instead of simply relying on out-of-the-box ML functions.
