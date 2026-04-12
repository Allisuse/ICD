<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>ICD Detector</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #0a0e1a;
    color: #e0e8ff;
    font-family: 'Segoe UI', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  header {
    padding: 18px 16px 10px;
    text-align: center;
  }
  header h1 {
    font-size: 18px;
    font-weight: 600;
    color: #00d4ff;
    letter-spacing: 0.5px;
  }
  header p {
    font-size: 13px;
    color: #7a9cc0;
    margin-top: 4px;
  }

  #camera-wrap {
    position: relative;
    width: 100%;
    max-width: 480px;
    background: #000;
  }

  #video {
    width: 100%;
    display: block;
    object-fit: cover;
  }

  #overlay {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
  }

  #controls {
    width: 100%;
    max-width: 480px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  #snapBtn {
    width: 100%;
    padding: 14px;
    background: #00d4ff;
    color: #000;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    letter-spacing: 0.3px;
  }
  #snapBtn:active { opacity: 0.8; }

  #result {
    text-align: center;
    font-size: 42px;
    font-weight: 700;
    color: #00ff88;
    display: none;
    padding: 8px 0;
  }

  #error {
    background: #2a0a0a;
    border: 1px solid #ff4444;
    color: #ff8888;
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 14px;
    display: none;
  }

  #snap-preview-wrap {
    position: relative;
    width: 100%;
    max-width: 480px;
    display: none;
  }
  #snap-preview {
    width: 100%;
    display: block;
    border-radius: 8px;
  }

  #retakeBtn {
    width: 100%;
    padding: 12px;
    background: transparent;
    color: #00d4ff;
    border: 1px solid #00d4ff;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    display: none;
  }
  #retakeBtn:active { opacity: 0.7; }

  #permission-error {
    max-width: 360px;
    margin: 40px 16px;
    background: #1a1020;
    border: 1px solid #553366;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    display: none;
  }
  #permission-error h2 { color: #cc88ff; font-size: 16px; margin-bottom: 10px; }
  #permission-error p  { font-size: 14px; color: #9988aa; line-height: 1.6; }
</style>
</head>
<body>

<header>
  <h1>💧 ICD Volume Detector</h1>
  <p>เล็งขีดขวดให้ตรงเส้นสีแดง</p>
</header>

<div id="camera-wrap">
  <video id="video" autoplay playsinline muted></video>
  <canvas id="overlay"></canvas>
</div>

<div id="permission-error">
  <h2>ไม่สามารถเข้าถึงกล้องได้</h2>
  <p>กรุณาอนุญาตให้เบราว์เซอร์ใช้กล้อง แล้วรีโหลดหน้านี้<br><br>
     Chrome: แตะไอคอนกล้องในแถบที่อยู่ → Allow<br>
     Safari: Settings → Safari → Camera → Allow
  </p>
</div>

<div id="snap-preview-wrap">
  <canvas id="snap-preview"></canvas>
</div>

<div id="controls">
  <div id="result"></div>
  <div id="error"></div>
  <button id="snapBtn">📸 ถ่ายรูปวิเคราะห์</button>
  <button id="retakeBtn">🔄 ถ่ายใหม่</button>
</div>

<script>
const video      = document.getElementById('video');
const overlay    = document.getElementById('overlay');
const snapCanvas = document.getElementById('snap-preview');
const ctx        = overlay.getContext('2d');
const snapCtx    = snapCanvas.getContext('2d');
const snapBtn    = document.getElementById('snapBtn');
const retakeBtn  = document.getElementById('retakeBtn');
const resultEl   = document.getElementById('result');
const errorEl    = document.getElementById('error');
const snapWrap   = document.getElementById('snap-preview-wrap');
const permErr    = document.getElementById('permission-error');
const cameraWrap = document.getElementById('camera-wrap');

// --- Guide line positions (fraction of frame height) ---
const LINE_TOP = 0.35;   // 900 ml mark
const LINE_BOT = 0.65;   // 100 ml mark

// Start camera — prefer rear camera on mobile
async function startCamera() {
  const constraints = [
    { video: { facingMode: { exact: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } } },
    { video: { facingMode: 'environment' } },
    { video: true }
  ];
  for (const c of constraints) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia(c);
      video.srcObject = stream;
      return;
    } catch(e) {}
  }
  cameraWrap.style.display = 'none';
  permErr.style.display = 'block';
  snapBtn.style.display = 'none';
}

startCamera();

// Draw guide lines on video overlay every frame
function drawGuide() {
  const W = video.videoWidth  || video.clientWidth  || 480;
  const H = video.videoHeight || video.clientHeight || 360;
  overlay.width  = W;
  overlay.height = H;

  const y900 = Math.round(H * LINE_TOP);
  const y100 = Math.round(H * LINE_BOT);

  ctx.clearRect(0, 0, W, H);

  // Semi-transparent zone between lines
  ctx.fillStyle = 'rgba(255, 0, 0, 0.06)';
  ctx.fillRect(0, y900, W, y100 - y900);

  // Red lines
  ctx.strokeStyle = '#ff2222';
  ctx.lineWidth   = 3;
  ctx.setLineDash([]);

  ctx.beginPath(); ctx.moveTo(0, y900); ctx.lineTo(W, y900); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0, y100); ctx.lineTo(W, y100); ctx.stroke();

  // Side tick marks
  const tick = 18;
  ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(0, y900 - tick); ctx.lineTo(0, y900 + tick); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(W, y900 - tick); ctx.lineTo(W, y900 + tick); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0, y100 - tick); ctx.lineTo(0, y100 + tick); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(W, y100 - tick); ctx.lineTo(W, y100 + tick); ctx.stroke();

  // Labels — white text with dark pill background
  function label(text, y, align) {
    const pad = 8, fh = 22, fw = ctx.measureText(text).width + pad * 2;
    const x = align === 'right' ? W - fw - 6 : 6;
    ctx.fillStyle = 'rgba(0,0,0,0.65)';
    roundRect(ctx, x, y - fh + 4, fw, fh, 5);
    ctx.fill();
    ctx.fillStyle = '#ff6666';
    ctx.font = 'bold 13px Segoe UI, sans-serif';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x + pad, y - 3);
  }

  label('900 ml', y900, 'left');
  label('100 ml', y100, 'left');

  requestAnimationFrame(drawGuide);
}

function roundRect(c, x, y, w, h, r) {
  c.beginPath();
  c.moveTo(x + r, y);
  c.lineTo(x + w - r, y); c.quadraticCurveTo(x + w, y, x + w, y + r);
  c.lineTo(x + w, y + h - r); c.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  c.lineTo(x + r, y + h); c.quadraticCurveTo(x, y + h, x, y + h - r);
  c.lineTo(x, y + r); c.quadraticCurveTo(x, y, x + r, y);
  c.closePath();
}

video.addEventListener('loadedmetadata', drawGuide);
if (video.readyState >= 1) drawGuide();

// --- Snap + analyse ---
snapBtn.addEventListener('click', () => {
  const W = video.videoWidth;
  const H = video.videoHeight;
  if (!W || !H) { showError('กล้องยังไม่พร้อม ลองใหม่อีกครั้ง'); return; }

  snapCanvas.width  = W;
  snapCanvas.height = H;
  snapCtx.drawImage(video, 0, 0, W, H);

  const px900 = Math.round(H * LINE_TOP);
  const px100 = Math.round(H * LINE_BOT);

  // Draw guide lines on snapshot too
  snapCtx.strokeStyle = '#ff2222';
  snapCtx.lineWidth   = 4;
  snapCtx.beginPath(); snapCtx.moveTo(0, px900); snapCtx.lineTo(W, px900); snapCtx.stroke();
  snapCtx.beginPath(); snapCtx.moveTo(0, px100); snapCtx.lineTo(W, px100); snapCtx.stroke();

  // Analyse with edge detection
  const detected = findWaterLine(snapCtx, W, H, px900, px100);

  if (detected !== null) {
    // Draw detected line in green
    snapCtx.strokeStyle = '#00ff88';
    snapCtx.lineWidth   = 6;
    snapCtx.beginPath();
    snapCtx.moveTo(0, detected);
    snapCtx.lineTo(W, detected);
    snapCtx.stroke();

    const volume = 100 + ((px100 - detected) / (px100 - px900) * 800);
    showResult(Math.round(Math.max(0, Math.min(1000, volume))));
  } else {
    showError('หาผิวน้ำไม่เจอ — ลองขยับให้ขีด 900 ตรงเส้นแดงบน แสงควรสว่างพอ');
  }

  // Show snapshot
  snapWrap.style.display = 'block';
  cameraWrap.style.display = 'none';
  snapBtn.style.display = 'none';
  retakeBtn.style.display = 'block';
});

retakeBtn.addEventListener('click', () => {
  snapWrap.style.display = 'none';
  cameraWrap.style.display = 'block';
  snapBtn.style.display = 'block';
  retakeBtn.style.display = 'none';
  resultEl.style.display = 'none';
  errorEl.style.display = 'none';
});

// Simple horizontal edge detection on the search strip
function findWaterLine(sctx, W, H, px900, px100) {
  const margin = 60;
  const searchTop = Math.max(0, px900 - margin);
  const searchBot = Math.min(H - 1, px100 + margin);
  const stripH = searchBot - searchTop;
  if (stripH <= 0) return null;

  const imgData = sctx.getImageData(0, searchTop, W, stripH);
  const data    = imgData.data;

  // For each row compute mean brightness change (horizontal gradient)
  const scores = new Float32Array(stripH);
  for (let y = 1; y < stripH - 1; y++) {
    let score = 0;
    const step = Math.max(1, Math.floor(W / 80)); // sample ~80 points
    for (let x = 0; x < W; x += step) {
      const i  = (y * W + x) * 4;
      const iu = ((y - 1) * W + x) * 4;
      const id = ((y + 1) * W + x) * 4;
      const bright  = (data[i]  + data[i+1]  + data[i+2])  / 3;
      const brightU = (data[iu] + data[iu+1] + data[iu+2]) / 3;
      const brightD = (data[id] + data[id+1] + data[id+2]) / 3;
      score += Math.abs(bright - brightU) + Math.abs(bright - brightD);
    }
    scores[y] = score;
  }

  // Find row with max edge score that is roughly horizontal
  let best = -1, bestScore = 0;
  for (let y = 2; y < stripH - 2; y++) {
    const s = scores[y];
    if (s > bestScore) { bestScore = s; best = y; }
  }

  // Threshold: reject if signal is too weak
  const mean = scores.reduce((a, b) => a + b, 0) / stripH;
  if (best === -1 || bestScore < mean * 1.8) return null;

  return searchTop + best;
}

function showResult(ml) {
  resultEl.textContent = ml + ' ml';
  resultEl.style.display = 'block';
  errorEl.style.display  = 'none';
}

function showError(msg) {
  errorEl.textContent   = '❌ ' + msg;
  errorEl.style.display = 'block';
  resultEl.style.display = 'none';
}
</script>
</body>
</html>
