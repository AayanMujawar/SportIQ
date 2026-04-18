/**
 * SportIQ — Frontend Application
 * Handles video upload, API communication, and result display
 * for the AI-Powered Cricket Performance Analyzer.
 */

// ═══════════════════════════════════════════════════════════════
//  Configuration
// ═══════════════════════════════════════════════════════════════

const CONFIG = {
  // Change this URL to your Render deployment URL in production
  // e.g., 'https://sportiq-backend.onrender.com'
  API_BASE_URL: 'http://localhost:8000',
  API_PREFIX: '/api/v1',
  MAX_FILE_SIZE_MB: 50,
  MAX_FILE_SIZE_BYTES: 50 * 1024 * 1024,
  ALLOWED_EXTENSIONS: ['.mp4', '.avi', '.mov', '.webm', '.mkv'],
  ALLOWED_MIME_TYPES: [
    'video/mp4', 'video/avi', 'video/x-msvideo',
    'video/quicktime', 'video/webm', 'video/x-matroska'
  ],
};

// ═══════════════════════════════════════════════════════════════
//  State Management
// ═══════════════════════════════════════════════════════════════

const state = {
  selectedFile: null,
  isProcessing: false,
  currentSection: 'upload', // 'upload' | 'processing' | 'results'
};

// ═══════════════════════════════════════════════════════════════
//  DOM Elements
// ═══════════════════════════════════════════════════════════════

const DOM = {};

function cacheDOMElements() {
  DOM.navbar = document.getElementById('navbar');
  DOM.dropZone = document.getElementById('drop-zone');
  DOM.fileInput = document.getElementById('file-input');
  DOM.filePreview = document.getElementById('file-preview');
  DOM.filePreviewName = document.getElementById('file-preview-name');
  DOM.filePreviewSize = document.getElementById('file-preview-size');
  DOM.fileRemoveBtn = document.getElementById('file-remove-btn');
  DOM.sportSelect = document.getElementById('sport-select');
  DOM.shotSelect = document.getElementById('shot-select');
  DOM.uploadBtn = document.getElementById('upload-btn');
  DOM.uploadSection = document.getElementById('upload-section');
  DOM.processingSection = document.getElementById('processing-section');
  DOM.processingStatus = document.getElementById('processing-status');
  DOM.progressBar = document.getElementById('progress-bar');
  DOM.resultsSection = document.getElementById('results-section');
  DOM.originalVideo = document.getElementById('original-video');
  DOM.processedVideo = document.getElementById('processed-video');
  DOM.statFrames = document.getElementById('stat-frames');
  DOM.statDetection = document.getElementById('stat-detection');
  DOM.statTime = document.getElementById('stat-time');
  DOM.statFps = document.getElementById('stat-fps');
  DOM.newAnalysisBtn = document.getElementById('new-analysis-btn');
  DOM.toastContainer = document.getElementById('toast-container');
}

// ═══════════════════════════════════════════════════════════════
//  Event Listeners
// ═══════════════════════════════════════════════════════════════

function initEventListeners() {
  // ── Navbar scroll effect ────────────────────────────────
  window.addEventListener('scroll', () => {
    DOM.navbar.classList.toggle('scrolled', window.scrollY > 50);
  });

  // ── Smooth scroll for nav links ─────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── Drop Zone: Click to browse ──────────────────────────
  DOM.dropZone.addEventListener('click', () => {
    DOM.fileInput.click();
  });

  // ── Drop Zone: Drag & Drop ──────────────────────────────
  DOM.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    DOM.dropZone.classList.add('drag-over');
  });

  DOM.dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    DOM.dropZone.classList.remove('drag-over');
  });

  DOM.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    DOM.dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  });

  // ── File Input Change ───────────────────────────────────
  DOM.fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  // ── Remove File ─────────────────────────────────────────
  DOM.fileRemoveBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearFileSelection();
  });

  // ── Upload Button ───────────────────────────────────────
  DOM.uploadBtn.addEventListener('click', () => {
    if (state.selectedFile && !state.isProcessing) {
      uploadAndProcess();
    }
  });

  // ── New Analysis Button ─────────────────────────────────
  DOM.newAnalysisBtn.addEventListener('click', () => {
    resetToUpload();
  });
}

// ═══════════════════════════════════════════════════════════════
//  File Handling
// ═══════════════════════════════════════════════════════════════

function handleFileSelection(file) {
  // Validate file type
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!CONFIG.ALLOWED_EXTENSIONS.includes(ext)) {
    showToast(`Invalid file type: ${ext}. Supported: ${CONFIG.ALLOWED_EXTENSIONS.join(', ')}`, 'error');
    return;
  }

  // Validate file size
  if (file.size > CONFIG.MAX_FILE_SIZE_BYTES) {
    const sizeMB = (file.size / 1024 / 1024).toFixed(1);
    showToast(`File too large: ${sizeMB}MB. Max: ${CONFIG.MAX_FILE_SIZE_MB}MB`, 'error');
    return;
  }

  state.selectedFile = file;

  // Update UI
  DOM.filePreviewName.textContent = file.name;
  DOM.filePreviewSize.textContent = formatFileSize(file.size);
  DOM.filePreview.classList.add('visible');
  DOM.uploadBtn.disabled = false;
  DOM.dropZone.style.display = 'none';

  showToast(`Selected: ${file.name}`, 'success');
}

function clearFileSelection() {
  state.selectedFile = null;
  DOM.fileInput.value = '';
  DOM.filePreview.classList.remove('visible');
  DOM.uploadBtn.disabled = true;
  DOM.dropZone.style.display = 'block';
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ═══════════════════════════════════════════════════════════════
//  Upload & Processing
// ═══════════════════════════════════════════════════════════════

async function uploadAndProcess() {
  if (!state.selectedFile || state.isProcessing) return;

  state.isProcessing = true;
  showSection('processing');

  const formData = new FormData();
  formData.append('file', state.selectedFile);
  formData.append('sport', DOM.sportSelect.value);
  formData.append('shot_type', DOM.shotSelect.value);

  // Simulate progress stages
  const progressStages = [
    { percent: 10, text: 'Uploading video to server...' },
    { percent: 25, text: 'Initializing MediaPipe pose model...' },
    { percent: 40, text: 'Analyzing body pose frame by frame...' },
    { percent: 60, text: 'Drawing skeleton overlay...' },
    { percent: 75, text: 'Extracting keypoint coordinates...' },
    { percent: 85, text: 'Rendering output video...' },
    { percent: 95, text: 'Finalizing results...' },
  ];

  // Start progress simulation
  let stageIndex = 0;
  const progressInterval = setInterval(() => {
    if (stageIndex < progressStages.length) {
      const stage = progressStages[stageIndex];
      updateProgress(stage.percent, stage.text);
      stageIndex++;
    }
  }, 2500);

  try {
    updateProgress(5, 'Connecting to server...');

    const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/upload`, {
      method: 'POST',
      body: formData,
    });

    clearInterval(progressInterval);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: { message: 'Unknown error' } }));
      throw new Error(errorData.detail?.message || `Server error: ${response.status}`);
    }

    const result = await response.json();

    if (result.status === 'success') {
      updateProgress(100, 'Complete!');
      
      // Short delay to show 100% completion
      await new Promise(resolve => setTimeout(resolve, 800));
      
      displayResults(result.data);
      showToast('🏏 Video processed successfully!', 'success');
    } else {
      throw new Error(result.message || 'Processing failed');
    }

  } catch (error) {
    clearInterval(progressInterval);
    console.error('Upload error:', error);

    let errorMsg = error.message;
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      errorMsg = 'Cannot connect to server. Make sure the backend is running on ' + CONFIG.API_BASE_URL;
    }

    showToast(`Error: ${errorMsg}`, 'error');
    
    // Instead of hiding everything, show the error clearly on screen
    DOM.processingStatus.innerHTML = `<span style="color: var(--accent-red); font-weight: bold;">❌ Error: ${errorMsg}</span>`;
    DOM.progressBar.style.background = 'var(--accent-red)';
    
    // Give user a button to go back
    if (!document.getElementById('error-back-btn')) {
      const backBtn = document.createElement('button');
      backBtn.id = 'error-back-btn';
      backBtn.className = 'btn btn-secondary';
      backBtn.style.marginTop = '20px';
      backBtn.innerHTML = '← Try Again';
      backBtn.onclick = () => {
        backBtn.remove();
        DOM.progressBar.style.background = '';
        resetToUpload();
      };
      DOM.processingSection.appendChild(backBtn);
    }
  } finally {
    state.isProcessing = false;
  }
}

function updateProgress(percent, statusText) {
  DOM.progressBar.style.width = `${percent}%`;
  if (statusText) {
    DOM.processingStatus.textContent = statusText;
  }
}

// ═══════════════════════════════════════════════════════════════
//  Results Display
// ═══════════════════════════════════════════════════════════════

function displayResults(data) {
  // Set original video (from local file)
  if (state.selectedFile) {
    const objectURL = URL.createObjectURL(state.selectedFile);
    DOM.originalVideo.src = objectURL;
    DOM.originalVideo.style.display = 'block';
      const placeholder = DOM.originalVideo.parentElement.querySelector('.video-placeholder');
      if (placeholder) placeholder.style.display = 'none';
    }

  // Set processed video (from server)
  if (data.video_url) {
    const videoURL = `${CONFIG.API_BASE_URL}${data.video_url}`;
    DOM.processedVideo.src = videoURL;
    DOM.processedVideo.style.display = 'block';
      const placeholder = DOM.processedVideo.parentElement.querySelector('.video-placeholder');
      if (placeholder) placeholder.style.display = 'none';
    }

  // Update stats with count-up animation
  const stats = data.stats;
  if (stats) {
    animateValue(DOM.statFrames, 0, stats.total_frames || 0, 1000);
    animateValue(DOM.statDetection, 0, stats.detection_rate_percent || 0, 1000, '%');
    animateValue(DOM.statTime, 0, stats.processing_time_seconds || 0, 1000, 's');
    animateValue(DOM.statFps, 0, stats.fps || 0, 800);
  }

  showSection('results');

  // Scroll to results
  setTimeout(() => {
    DOM.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 200);
}

function animateValue(element, start, end, duration, suffix = '') {
  const startTime = performance.now();
  const isFloat = !Number.isInteger(end);

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + (end - start) * eased;

    element.textContent = (isFloat ? current.toFixed(1) : Math.round(current)) + suffix;

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

// ═══════════════════════════════════════════════════════════════
//  Section Navigation
// ═══════════════════════════════════════════════════════════════

function showSection(section) {
  state.currentSection = section;

  DOM.uploadSection.style.display = section === 'upload' ? 'block' : 'none';
  DOM.processingSection.classList.toggle('visible', section === 'processing');
  DOM.resultsSection.classList.toggle('visible', section === 'results');

  if (section === 'processing') {
    DOM.processingSection.style.display = 'block';
    DOM.resultsSection.style.display = 'none';
  } else if (section === 'results') {
    DOM.processingSection.style.display = 'none';
    DOM.resultsSection.style.display = 'block';
  } else {
    DOM.processingSection.style.display = 'none';
    DOM.resultsSection.style.display = 'none';
  }
}

function resetToUpload() {
  // Revoke object URLs to free memory
  if (DOM.originalVideo.src) {
    URL.revokeObjectURL(DOM.originalVideo.src);
    DOM.originalVideo.src = '';
    DOM.originalVideo.style.display = 'none';
  }
  DOM.processedVideo.src = '';
  DOM.processedVideo.style.display = 'none';

  // Restore placeholders
  const origPlaceholder = DOM.originalVideo.parentElement.querySelector('.video-placeholder');
  if (origPlaceholder) origPlaceholder.style.display = 'block';
  
  const procPlaceholder = DOM.processedVideo.parentElement.querySelector('.video-placeholder');
  if (procPlaceholder) procPlaceholder.style.display = 'block';

  // Reset stats
  DOM.statFrames.textContent = '0';
  DOM.statDetection.textContent = '0%';
  DOM.statTime.textContent = '0s';
  DOM.statFps.textContent = '0';

  // Reset progress
  updateProgress(0, '');

  // Reset file selection
  clearFileSelection();

  // Show upload section
  showSection('upload');

  // Scroll to upload
  DOM.uploadSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ═══════════════════════════════════════════════════════════════
//  Toast Notifications
// ═══════════════════════════════════════════════════════════════

function showToast(message, type = 'info') {
  const icons = {
    success: '✅',
    error: '❌',
    info: 'ℹ️',
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${icons[type] || icons.info}</span>
    <span>${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
  `;

  DOM.toastContainer.appendChild(toast);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (toast.parentElement) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }
  }, 5000);
}

// ═══════════════════════════════════════════════════════════════
//  Intersection Observer (Scroll Animations)
// ═══════════════════════════════════════════════════════════════

function initScrollAnimations() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll('.feature-card, .upload-card').forEach((el) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });
}

// Add the animate-in styles dynamically
const style = document.createElement('style');
style.textContent = `
  .animate-in {
    opacity: 1 !important;
    transform: translateY(0) !important;
  }
`;
document.head.appendChild(style);

// ═══════════════════════════════════════════════════════════════
//  API Health Check
// ═══════════════════════════════════════════════════════════════

async function checkBackendStatus() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/health`, {
      signal: AbortSignal.timeout(5000),
    });
    if (response.ok) {
      console.log('✅ SportIQ backend connected');
      return true;
    }
  } catch (e) {
    console.warn('⚠️ Backend not reachable at', CONFIG.API_BASE_URL);
    console.warn('   Start the backend: cd backend && uvicorn main:app --reload');
  }
  return false;
}

// ═══════════════════════════════════════════════════════════════
//  Initialize
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  cacheDOMElements();
  initEventListeners();
  initScrollAnimations();
  checkBackendStatus();

  console.log('🏏 SportIQ — Cricket Shot Analyzer initialized');
  console.log(`   API: ${CONFIG.API_BASE_URL}`);
});
