/**
 * SportIQ — Frontend Application (50% Project Dashboard)
 */

const CONFIG = {
  API_BASE_URL: 'http://localhost:8000',
  API_PREFIX: '/api/v1',
  MAX_FILE_SIZE_MB: 50,
  MAX_FILE_SIZE_BYTES: 50 * 1024 * 1024,
  ALLOWED_EXTENSIONS: ['.mp4', '.avi', '.mov', '.webm', '.mkv'],
};

const state = { selectedFile: null, isProcessing: false, currentSection: 'upload', lastResultData: null };
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
  DOM.statErrorRate = document.getElementById('stat-errorrate');
  DOM.statFrames = document.getElementById('stat-frames');
  DOM.statDetection = document.getElementById('stat-detection');
  DOM.statTime = document.getElementById('stat-time');
  DOM.statFps = document.getElementById('stat-fps');
  DOM.newAnalysisBtn = document.getElementById('new-analysis-btn');
  DOM.toastContainer = document.getElementById('toast-container');
  DOM.dashShotIcon = document.getElementById('dash-shot-icon');
  DOM.dashShotName = document.getElementById('dash-shot-name');
  DOM.dashShotMethod = document.getElementById('dash-shot-method');
  DOM.gaugeCanvas = document.getElementById('gauge-canvas');
  DOM.gaugeValue = document.getElementById('gauge-value');
  DOM.gradeLetter = document.getElementById('grade-letter');
  DOM.jointBarsContainer = document.getElementById('joint-bars-container');
  DOM.radarCanvas = document.getElementById('radar-canvas');
  DOM.coachingGrid = document.getElementById('coaching-grid');
  DOM.timelinePanel = document.getElementById('timeline-panel');
  DOM.syncPlayBtn = document.getElementById('sync-play-btn');
  DOM.downloadReportBtn = document.getElementById('download-report-btn');
}

function initEventListeners() {
  window.addEventListener('scroll', () => DOM.navbar.classList.toggle('scrolled', window.scrollY > 50));
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => { e.preventDefault(); const t = document.querySelector(link.getAttribute('href')); if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
  });
  DOM.dropZone.addEventListener('click', () => DOM.fileInput.click());
  DOM.dropZone.addEventListener('dragover', (e) => { e.preventDefault(); DOM.dropZone.classList.add('drag-over'); });
  DOM.dropZone.addEventListener('dragleave', (e) => { e.preventDefault(); DOM.dropZone.classList.remove('drag-over'); });
  DOM.dropZone.addEventListener('drop', (e) => { e.preventDefault(); DOM.dropZone.classList.remove('drag-over'); if (e.dataTransfer.files.length > 0) handleFileSelection(e.dataTransfer.files[0]); });
  DOM.fileInput.addEventListener('change', (e) => { if (e.target.files.length > 0) handleFileSelection(e.target.files[0]); });
  DOM.fileRemoveBtn.addEventListener('click', (e) => { e.stopPropagation(); clearFileSelection(); });
  DOM.uploadBtn.addEventListener('click', () => { if (state.selectedFile && !state.isProcessing) uploadAndProcess(); });
  DOM.newAnalysisBtn.addEventListener('click', () => resetToUpload());
  DOM.syncPlayBtn.addEventListener('click', () => syncPlayVideos());
  DOM.downloadReportBtn.addEventListener('click', () => downloadReport());
}

function handleFileSelection(file) {
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!CONFIG.ALLOWED_EXTENSIONS.includes(ext)) { showToast(`Invalid file type: ${ext}`, 'error'); return; }
  if (file.size > CONFIG.MAX_FILE_SIZE_BYTES) { showToast(`File too large: ${(file.size/1024/1024).toFixed(1)}MB`, 'error'); return; }
  state.selectedFile = file;
  DOM.filePreviewName.textContent = file.name;
  DOM.filePreviewSize.textContent = formatFileSize(file.size);
  DOM.filePreview.classList.add('visible');
  DOM.uploadBtn.disabled = false;
  DOM.dropZone.style.display = 'none';
  showToast(`Selected: ${file.name}`, 'success');
}

function clearFileSelection() {
  state.selectedFile = null; DOM.fileInput.value = '';
  DOM.filePreview.classList.remove('visible'); DOM.uploadBtn.disabled = true; DOM.dropZone.style.display = 'block';
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function uploadAndProcess() {
  if (!state.selectedFile || state.isProcessing) return;
  state.isProcessing = true;
  showSection('processing');
  const formData = new FormData();
  formData.append('file', state.selectedFile);
  formData.append('sport', DOM.sportSelect.value);
  formData.append('shot_type', DOM.shotSelect.value);
  const stages = [
    { percent: 10, text: 'Uploading video to server...' }, { percent: 30, text: 'Initializing MediaPipe pose model...' },
    { percent: 50, text: 'Analyzing body pose frame by frame...' }, { percent: 70, text: 'Calculating joint angle deviations...' },
    { percent: 85, text: 'Generating coaching tips & injury prevention...' }, { percent: 90, text: 'Rendering output video...' },
    { percent: 95, text: 'Finalizing results...' },
  ];
  let si = 0;
  const pi = setInterval(() => { if (si < stages.length) { updateProgress(stages[si].percent, stages[si].text); si++; } }, 2500);
  try {
    updateProgress(5, 'Connecting to server...');
    const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_PREFIX}/upload`, { method: 'POST', body: formData });
    clearInterval(pi);
    if (!response.ok) { const ed = await response.json().catch(() => ({ detail: { message: 'Unknown error' } })); throw new Error(ed.detail?.message || `Server error: ${response.status}`); }
    const result = await response.json();
    if (result.status === 'success') {
      updateProgress(100, 'Complete!');
      await new Promise(r => setTimeout(r, 800));
      displayResults(result.data);
      showToast('🏏 Video analyzed successfully!', 'success');
    } else { throw new Error(result.message || 'Processing failed'); }
  } catch (error) {
    clearInterval(pi); console.error('Upload error:', error);
    let msg = error.message;
    if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) msg = 'Cannot connect to server. Make sure backend is running on ' + CONFIG.API_BASE_URL;
    showToast(`Error: ${msg}`, 'error');
    DOM.processingStatus.innerHTML = `<span style="color: var(--accent-red); font-weight: bold;">❌ Error: ${msg}</span>`;
    DOM.progressBar.style.background = 'var(--accent-red)';
    if (!document.getElementById('error-back-btn')) {
      const b = document.createElement('button'); b.id = 'error-back-btn'; b.className = 'btn btn-secondary'; b.style.marginTop = '20px'; b.innerHTML = '← Try Again';
      b.onclick = () => { b.remove(); DOM.progressBar.style.background = ''; resetToUpload(); }; DOM.processingSection.appendChild(b);
    }
  } finally { state.isProcessing = false; }
}

function updateProgress(p, t) { DOM.progressBar.style.width = `${p}%`; if (t) DOM.processingStatus.textContent = t; }

// ═══════════════════════════════════════════════════════════════
//  Results Dashboard
// ═══════════════════════════════════════════════════════════════

function displayResults(data) {
  state.lastResultData = data;

  // Videos
  if (state.selectedFile) {
    const url = URL.createObjectURL(state.selectedFile);
    DOM.originalVideo.src = url; DOM.originalVideo.style.display = 'block';
    const p = DOM.originalVideo.parentElement.querySelector('.video-placeholder'); if (p) p.style.display = 'none';
  }
  if (data.video_url) {
    DOM.processedVideo.src = `${CONFIG.API_BASE_URL}${data.video_url}`;
    DOM.processedVideo.style.display = 'block';
    const p = DOM.processedVideo.parentElement.querySelector('.video-placeholder'); if (p) p.style.display = 'none';
  }

  // Shot classification
  const shot = data.shot_classification || {};
  DOM.dashShotIcon.textContent = shot.icon || '🏏';
  DOM.dashShotName.textContent = shot.display_name || 'Cricket Shot';
  DOM.dashShotMethod.textContent = shot.method === 'auto_detected' ? `AI Detected • ${Math.round((shot.confidence||0)*100)}% confidence` : 'User Selected';

  // Performance grade
  const analysis = data.analysis || {};
  const grade = analysis.performance_grade || 'N/A';
  DOM.gradeLetter.textContent = grade;
  DOM.gradeLetter.className = 'grade-letter';
  if (grade.startsWith('A')) DOM.gradeLetter.classList.add('grade-a');
  else if (grade.startsWith('B')) DOM.gradeLetter.classList.add('grade-b');
  else if (grade.startsWith('C')) DOM.gradeLetter.classList.add('grade-c');
  else if (grade.startsWith('D')) DOM.gradeLetter.classList.add('grade-d');
  else DOM.gradeLetter.classList.add('grade-f');

  // Score gauge
  const score = analysis.overall_score || 0;
  animateGauge(score);

  // Stats
  const stats = data.stats;
  if (stats) {
    animateValue(DOM.statErrorRate, 0, stats.posture_error_rate || 0, 1000, '%');
    animateValue(DOM.statFrames, 0, stats.total_frames || 0, 1000);
    animateValue(DOM.statDetection, 0, stats.detection_rate_percent || 0, 1000, '%');
    animateValue(DOM.statTime, 0, stats.processing_time_seconds || 0, 1000, 's');
    animateValue(DOM.statFps, 0, stats.fps || 0, 800);
  }

  // Joint bars
  renderJointBars(analysis.joint_details || []);

  // Radar chart
  renderRadarChart(analysis.joint_details || []);

  // Coaching tips
  renderCoachingTips(analysis.coaching_tips || []);

  // Timeline
  renderTimeline(data.angle_timeline || {});

  showSection('results');
  setTimeout(() => DOM.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' }), 200);
}

// ── Animated Gauge ───────────────────────────────────────────

function animateGauge(targetScore) {
  const canvas = DOM.gaugeCanvas;
  const ctx = canvas.getContext('2d');
  const cx = 90, cy = 90, r = 72, lw = 10;
  const startAngle = 0.75 * Math.PI;
  const fullArc = 1.5 * Math.PI;
  let current = 0;
  const duration = 1200;
  const startTime = performance.now();

  function getColor(v) {
    if (v >= 80) return '#22c55e';
    if (v >= 60) return '#00d4aa';
    if (v >= 40) return '#f59e0b';
    return '#ef4444';
  }

  function draw(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    current = targetScore * (1 - Math.pow(1 - progress, 3));
    ctx.clearRect(0, 0, 180, 180);

    // Background arc
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, startAngle + fullArc);
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.stroke();

    // Colored arc
    const endAngle = startAngle + (current / 100) * fullArc;
    ctx.beginPath();
    ctx.arc(cx, cy, r, startAngle, endAngle);
    ctx.strokeStyle = getColor(current);
    ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.stroke();

    DOM.gaugeValue.textContent = Math.round(current) + '%';
    DOM.gaugeValue.style.color = getColor(current);

    if (progress < 1) requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
}

// ── Joint Progress Bars ──────────────────────────────────────

function renderJointBars(joints) {
  DOM.jointBarsContainer.innerHTML = '';
  if (!joints.length) { DOM.jointBarsContainer.innerHTML = '<div class="joint-bars-placeholder">No joint data available</div>'; return; }
  joints.forEach((j, i) => {
    const item = document.createElement('div');
    item.className = 'joint-bar-item';
    item.innerHTML = `
      <div class="joint-bar-label"><span class="joint-icon">${j.icon}</span> ${j.joint_label}</div>
      <div class="joint-bar-track"><div class="joint-bar-fill ${j.status}" id="jbar-${i}"></div></div>
      <div class="joint-bar-value">${j.score_percent}%</div>
    `;
    DOM.jointBarsContainer.appendChild(item);
    setTimeout(() => { document.getElementById(`jbar-${i}`).style.width = j.score_percent + '%'; }, 100 + i * 80);
  });
}

// ── Radar Chart ──────────────────────────────────────────────

function renderRadarChart(joints) {
  const canvas = DOM.radarCanvas;
  const ctx = canvas.getContext('2d');
  const cx = 160, cy = 160, maxR = 120;
  ctx.clearRect(0, 0, 320, 320);

  if (!joints.length) return;

  const n = joints.length;
  const angleStep = (2 * Math.PI) / n;

  // Draw grid rings
  for (let ring = 1; ring <= 4; ring++) {
    const rr = (maxR / 4) * ring;
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const a = -Math.PI / 2 + i * angleStep;
      const x = cx + rr * Math.cos(a), y = cy + rr * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = 'rgba(255,255,255,0.08)';
    ctx.lineWidth = 1; ctx.stroke();
  }

  // Draw axis lines & labels
  joints.forEach((j, i) => {
    const a = -Math.PI / 2 + i * angleStep;
    ctx.beginPath(); ctx.moveTo(cx, cy);
    ctx.lineTo(cx + maxR * Math.cos(a), cy + maxR * Math.sin(a));
    ctx.strokeStyle = 'rgba(255,255,255,0.06)'; ctx.lineWidth = 1; ctx.stroke();

    const lx = cx + (maxR + 20) * Math.cos(a), ly = cy + (maxR + 20) * Math.sin(a);
    ctx.fillStyle = '#8b95a8'; ctx.font = '10px Inter, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    const shortName = j.joint_label.replace('Left ', 'L.').replace('Right ', 'R.');
    ctx.fillText(shortName, lx, ly);
  });

  // Draw data polygon
  ctx.beginPath();
  joints.forEach((j, i) => {
    const a = -Math.PI / 2 + i * angleStep;
    const val = (j.score_percent / 100) * maxR;
    const x = cx + val * Math.cos(a), y = cy + val * Math.sin(a);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = 'rgba(0, 212, 170, 0.15)';
  ctx.fill();
  ctx.strokeStyle = '#00d4aa';
  ctx.lineWidth = 2; ctx.stroke();

  // Draw data points
  joints.forEach((j, i) => {
    const a = -Math.PI / 2 + i * angleStep;
    const val = (j.score_percent / 100) * maxR;
    const x = cx + val * Math.cos(a), y = cy + val * Math.sin(a);
    ctx.beginPath(); ctx.arc(x, y, 4, 0, 2 * Math.PI);
    ctx.fillStyle = '#00d4aa'; ctx.fill();
    ctx.strokeStyle = '#06070a'; ctx.lineWidth = 2; ctx.stroke();
  });
}

// ── Coaching Tips ────────────────────────────────────────────

function renderCoachingTips(tips) {
  DOM.coachingGrid.innerHTML = '';
  if (!tips.length) { DOM.coachingGrid.innerHTML = '<p style="color:var(--text-muted);text-align:center;">No coaching tips available</p>'; return; }
  tips.forEach(t => {
    const card = document.createElement('div');
    card.className = `coaching-card severity-${t.severity}`;
    card.innerHTML = `
      <div class="coaching-card-header">
        <span class="coaching-card-icon">${t.icon}</span>
        <span class="coaching-card-joint">${t.joint_label}</span>
        <span class="coaching-card-severity ${t.severity}">${t.severity === 'high' ? 'Needs Work' : t.severity === 'medium' ? 'Almost There' : 'Good Form'}</span>
      </div>
      <p class="coaching-card-tip">${t.tip}</p>
    `;
    DOM.coachingGrid.appendChild(card);
  });
}

// ── Angle Timeline Sparklines ────────────────────────────────

function renderTimeline(timeline) {
  DOM.timelinePanel.innerHTML = '';
  const joints = Object.keys(timeline);
  if (!joints.length) { DOM.timelinePanel.innerHTML = '<p style="color:var(--text-muted);text-align:center;grid-column:1/-1;">No timeline data available</p>'; return; }

  const LABEL_MAP = {
    left_elbow: 'Left Elbow', right_elbow: 'Right Elbow', left_knee: 'Left Knee', right_knee: 'Right Knee',
    left_shoulder: 'Left Shoulder', right_shoulder: 'Right Shoulder', left_hip: 'Left Hip', right_hip: 'Right Hip',
  };
  const COLORS = ['#00d4aa','#6366f1','#f59e0b','#ef4444','#00e5ff','#22c55e','#f97316','#a855f7'];

  joints.forEach((joint, idx) => {
    const points = timeline[joint];
    if (!points || points.length < 2) return;

    const card = document.createElement('div');
    card.className = 'timeline-card';
    const label = LABEL_MAP[joint] || joint.replace(/_/g, ' ');
    card.innerHTML = `<div class="timeline-card-label">${label}</div><canvas id="tl-${joint}" height="60"></canvas>`;
    DOM.timelinePanel.appendChild(card);

    requestAnimationFrame(() => {
      const canvas = document.getElementById(`tl-${joint}`);
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      canvas.width = canvas.offsetWidth;
      const w = canvas.width, h = 60;
      const vals = points.map(p => p.value);
      const minV = Math.min(...vals), maxV = Math.max(...vals);
      const range = maxV - minV || 1;
      const color = COLORS[idx % COLORS.length];

      ctx.beginPath();
      points.forEach((p, i) => {
        const x = (i / (points.length - 1)) * w;
        const y = h - 6 - ((p.value - minV) / range) * (h - 12);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.lineJoin = 'round'; ctx.stroke();

      // Fill below
      ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath();
      const grad = ctx.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, color + '30'); grad.addColorStop(1, color + '05');
      ctx.fillStyle = grad; ctx.fill();
    });
  });
}

// ── Video Sync ───────────────────────────────────────────────

function syncPlayVideos() {
  const v1 = DOM.originalVideo, v2 = DOM.processedVideo;
  if (!v1.src || !v2.src) { showToast('Both videos must be loaded', 'error'); return; }
  v1.currentTime = 0; v2.currentTime = 0;
  v1.play(); v2.play();
  showToast('▶️ Playing both videos in sync', 'info');
}

// ── Download Report ──────────────────────────────────────────

function downloadReport() {
  if (!state.lastResultData) { showToast('No results to download', 'error'); return; }
  const report = {
    project: 'SportIQ — Cricket Performance Analysis Report',
    generated_at: new Date().toISOString(),
    shot_classification: state.lastResultData.shot_classification,
    performance: state.lastResultData.analysis,
    stats: state.lastResultData.stats,
    angle_timeline: state.lastResultData.angle_timeline,
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = 'sportiq_report.json'; a.click();
  URL.revokeObjectURL(url);
  showToast('📥 Report downloaded!', 'success');
}

// ── Utilities ────────────────────────────────────────────────

function animateValue(el, start, end, dur, suffix = '') {
  const st = performance.now(); const isF = !Number.isInteger(end);
  function update(ct) {
    const p = Math.min((ct - st) / dur, 1);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = (isF ? (start + (end - start) * e).toFixed(1) : Math.round(start + (end - start) * e)) + suffix;
    if (p < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function showSection(section) {
  state.currentSection = section;
  DOM.uploadSection.style.display = section === 'upload' ? 'block' : 'none';
  DOM.processingSection.classList.toggle('visible', section === 'processing');
  DOM.resultsSection.classList.toggle('visible', section === 'results');
  DOM.processingSection.style.display = section === 'processing' ? 'block' : 'none';
  DOM.resultsSection.style.display = section === 'results' ? 'block' : 'none';
}

function resetToUpload() {
  if (DOM.originalVideo.src) { URL.revokeObjectURL(DOM.originalVideo.src); DOM.originalVideo.src = ''; DOM.originalVideo.style.display = 'none'; }
  DOM.processedVideo.src = ''; DOM.processedVideo.style.display = 'none';
  const op = DOM.originalVideo.parentElement.querySelector('.video-placeholder'); if (op) op.style.display = 'block';
  const pp = DOM.processedVideo.parentElement.querySelector('.video-placeholder'); if (pp) pp.style.display = 'block';
  if (DOM.statErrorRate) DOM.statErrorRate.textContent = '0%';
  DOM.statFrames.textContent = '0'; DOM.statDetection.textContent = '0%'; DOM.statTime.textContent = '0s'; DOM.statFps.textContent = '0';
  DOM.gaugeValue.textContent = '0%'; DOM.gradeLetter.textContent = '—';
  DOM.jointBarsContainer.innerHTML = '<div class="joint-bars-placeholder">Processing joint data...</div>';
  DOM.coachingGrid.innerHTML = ''; DOM.timelinePanel.innerHTML = '';
  state.lastResultData = null;
  updateProgress(0, ''); clearFileSelection(); showSection('upload');
  DOM.uploadSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showToast(message, type = 'info') {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span><button class="toast-close" onclick="this.parentElement.remove()">×</button>`;
  DOM.toastContainer.appendChild(toast);
  setTimeout(() => { if (toast.parentElement) { toast.style.opacity = '0'; toast.style.transform = 'translateX(100px)'; toast.style.transition = 'all 0.3s ease'; setTimeout(() => toast.remove(), 300); } }, 5000);
}

function initScrollAnimations() {
  const obs = new IntersectionObserver((entries) => { entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('animate-in'); obs.unobserve(e.target); } }); }, { threshold: 0.1 });
  document.querySelectorAll('.feature-card, .upload-card').forEach(el => { el.style.opacity = '0'; el.style.transform = 'translateY(20px)'; el.style.transition = 'opacity 0.6s ease, transform 0.6s ease'; obs.observe(el); });
}

const style = document.createElement('style');
style.textContent = `.animate-in { opacity: 1 !important; transform: translateY(0) !important; }`;
document.head.appendChild(style);

async function checkBackendStatus() {
  try { const r = await fetch(`${CONFIG.API_BASE_URL}/health`, { signal: AbortSignal.timeout(5000) }); if (r.ok) { console.log('✅ SportIQ backend connected'); return true; } } catch (e) { console.warn('⚠️ Backend not reachable at', CONFIG.API_BASE_URL); }
  return false;
}

document.addEventListener('DOMContentLoaded', () => {
  cacheDOMElements(); initEventListeners(); initScrollAnimations(); checkBackendStatus();
  console.log('🏏 SportIQ — Cricket Shot Analyzer initialized');
});
