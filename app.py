<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<title>ICD Detector</title>
<style>
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    -webkit-tap-highlight-color: transparent;
  }

  body {
    background: #080c16;
    color: #dde8ff;
    font-family: -apple-system, "Segoe UI", sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100svh;
    overscroll-behavior: none;
  }

  header {
    padding: 14px 16px 8px;
    text-align: center;
    width: 100%;
  }

  header h1 {
    font-size: 17px;
    font-weight: 600;
    color: #00d4ff;
  }

  header p {
    font-size: 12px;
    color: #607090;
    margin-top: 3px;
  }

  #video {
    display: none;
  }

  #live-canvas,
  #preview-canvas {
    width: 100%;
    max-width: 500px;
    display: block;
    background: #000;
    border-radius: 0;
    touch-action: manipulation;
  }

  #preview-canvas {
    display: none;
  }

  #controls {
    width: 100%;
    max-width: 500px;
    padding: 12px 14px 28px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  #result {
    text-align: center;
    font-size: 52px;
    font-weight: 700;
    color: #00ff88;
    display: none;
    padding: 4px 0;
    letter-spacing: -1px;
  }

  #error-msg {
    background: #1f0a0a;
    border: 1px solid #ff3333;
    color: #ff8080;
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 14px;
    line-height: 1.6;
    display: none;
    white-space: pre-line;
  }

  .btn-p {
    width: 100%;
    padding: 15px;
    background: #00d4ff;
    color: #000;
    border: none;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 700;
    cursor: pointer;
  }

  .btn-p:active {
    opacity: 0.75;
  }

  .btn-s {
    width: 100%;
    padding: 13px;
    background: transparent;
    color: #00d4ff;
    border: 1.5px solid #00d4ff;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    display: none;
  }

  .btn-s:active {
    opacity: 0.7;
  }

  #perm-screen {
    display: none;
    max-width: 320px;
    margin: 48px 20px;
    background: #12101e;
    border: 1px solid #332255;
    border-radius: 14px;
    padding: 28px 20px;
    text-align: center;
  }

  #perm-screen h2 {
    color: #bb88ff;
    font-size: 16px;
    margin-bottom: 10px;
  }

  #perm-screen p {
    font-size: 13px;
    color: #8877aa;
    line-height: 1.7;
  }

  #perm-screen button {
    margin-top: 16px;
    padding: 11px 22px;
    background: #553388;
    color: #fff;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    cursor: pointer;
  }

  #loading {
    width: 100%;
    max-width: 500px;
    height: 260px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #000;
    color: #607090;
    font-size: 14px;
  }
</style>
</head>
<body>

<header>
  <h1>💧 ICD Volume Detector</h1>
  <p>เล็งขีดขวดให้ตรงเส้นสีแดง แล้วกด "ถ่ายรูปวิเคราะห์"</p>
</header>

<video id="video" autoplay playsinline muted webkit-playsinline x5-playsinline></video>

<div id="loading">กำลังเปิดกล้อง…</div>

<div id="perm-screen">
  <h2>⚠️ ไม่สามารถเข้าถึงกล้องได้</h2>
  <p>
    ต้องเปิดผ่าน <b>https://</b> หรือ localhost<br><br>
    <b>iPhone/Safari:</b> Settings → Safari → Camera → Allow<br>
    <b>Android/Chrome:</b> แตะไอคอนกล้องในแถบที่อยู่ → Allow
  </p>
  <button onclick="location.reload()">🔄 ลองใหม่</button>
</div>

<canvas id="live-canvas"></canvas>
<canvas id="preview-canvas"></canvas>

<div id="controls">
  <div id="result"></div>
  <div id="error-msg"></div>
  <button class="btn-p" id="snap-btn">📸 ถ่ายรูปวิเคราะห์</button>
  <button class="btn-s" id="retake-btn">🔄 ถ่ายใหม่</button>
</div>

<script>
const LINE_TOP = 0.35;   // 900 ml
const LINE_BOT = 0.65;   // 100 ml

const video      = document.getElementById('video');
const liveCvs    = document.getElementById('live-canvas');
const lCtx       = liveCvs.getContext('2d', { willReadFrequently: true });

const prevCvs    = document.getElementById('preview-canvas');
const pCtx       = prevCvs.getContext('2d', { willReadFrequently: true });

const loading    = document.getElementById('loading');
const permScreen = document.getElementById('perm-screen');
const snapBtn    = document.getElementById('snap-btn');
const retakeBtn  = document.getElementById('retake-btn');
const resultEl   = document.getElementById('result');
const errorEl    = document.getElementById('error-msg');

// Canvas สำหรับวิเคราะห์แบบ “ไม่มีเส้นแดงทับ”
const rawCvs = document.createElement('canvas');
const rCtx   = rawCvs.getContext('2d', { willReadFrequently: true });

let loopRunning = false;
let currentStream = null;

video.setAttribute('playsinline', '');
video.setAttribute('webkit-playsinline', '');
video.muted = true;
video.autoplay = true;

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    showPerm();
    return;
  }

  const attempts = [
    { video: { facingMode: { exact: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
    { video: { facingMode: { exact: 'environment' } }, audio: false },
    { video: { facingMode: 'environment' }, audio: false },
    { video: true, audio: false }
  ];

  for (const c of attempts) {
    try {
      if (currentStream) {
        currentStream.getTracks().forEach(t => t.stop());
        currentStream = null;
      }

      const stream = await navigator.mediaDevices.getUserMedia(c);
      currentStream = stream;
      video.srcObject = stream;

      await video.play().catch(() => {});
      return;
    } catch (e) {
      if (e.name === 'NotAllowedError' || e.name === 'SecurityError') break;
    }
  }

  showPerm();
}

function showPerm() {
  loading.style.display = 'none';
  permScreen.style.display = 'block';
  snapBtn.style.display = 'none';
}

function onVideoReady() {
  if (loopRunning) return;
  loopRunning = true;
  loading.style.display = 'none';
  liveCvs.style.display = 'block';
  requestAnimationFrame(liveLoop);
}

video.addEventListener('loadedmetadata', onVideoReady);
video.addEventListener('canplay', onVideoReady);

startCamera();

function fitCanvasToVideo(canvas, W, H) {
  if (canvas.width !== W) canvas.width = W;
  if (canvas.height !== H) canvas.height = H;
}

function drawFrame(ctx, sourceVideo, W, H) {
  ctx.clearRect(0, 0, W, H);
  ctx.drawImage(sourceVideo, 0, 0, W, H);
}

function liveLoop() {
  const W = video.videoWidth;
  const H = video.videoHeight;

  if (!W || !H) {
    requestAnimationFrame(liveLoop);
    return;
  }

  fitCanvasToVideo(liveCvs, W, H);
  fitCanvasToVideo(rawCvs, W, H);

  // raw canvas = เอาไว้ตรวจจับอย่างเดียว ไม่มีเส้นแดง
  drawFrame(rCtx, video, W, H);

  // live canvas = ภาพจริง + overlay
  drawFrame(lCtx, video, W, H);
  drawGuideLines(lCtx, W, H);

  requestAnimationFrame(liveLoop);
}

function drawGuideLines(ctx, W, H) {
  const y900 = Math.round(H * LINE_TOP);
  const y100 = Math.round(H * LINE_BOT);
  const lw   = Math.max(4, Math.round(W * 0.007));

  ctx.save();

  ctx.fillStyle = 'rgba(255,20,20,0.10)';
  ctx.fillRect(0, y900, W, y100 - y900);

  ctx.strokeStyle = '#ff2020';
  ctx.lineWidth   = lw;

  ctx.beginPath();
  ctx.moveTo(0, y900);
  ctx.lineTo(W, y900);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(0, y100);
  ctx.lineTo(W, y100);
  ctx.stroke();

  const tick = Math.round(H * 0.045);
  ctx.lineWidth = lw + 2;

  [[0,y900],[W,y900],[0,y100],[W,y100]].forEach(([x,y]) => {
    ctx.beginPath();
    ctx.moveTo(x, y - tick);
    ctx.lineTo(x, y + tick);
    ctx.stroke();
  });

  const fs = Math.max(16, Math.round(H * 0.042));
  ctx.font = `bold ${fs}px -apple-system, sans-serif`;
  ctx.textBaseline = 'alphabetic';

  drawLabel(ctx, '▶ 900 ml', 12, y900 - 10, fs);
  drawLabel(ctx, '▶ 100 ml', 12, y100 - 10, fs);

  ctx.restore();
}

function drawLabel(ctx, text, x, y, fs) {
  const pad = 8;
  const tw = ctx.measureText(text).width;

  ctx.fillStyle = 'rgba(0,0,0,0.60)';
  if (ctx.roundRect) {
    ctx.beginPath();
    ctx.roundRect(x - pad, y - fs + 2, tw + pad * 2, fs + 8, 6);
    ctx.fill();
  } else {
    ctx.fillRect(x - pad, y - fs + 2, tw + pad * 2, fs + 8);
  }

  ctx.fillStyle = '#ff7070';
  ctx.fillText(text, x, y);
}

snapBtn.addEventListener('click', () => {
  const W = video.videoWidth;
  const H = video.videoHeight;

  if (!W || !H) {
    showError('กล้องยังไม่พร้อม');
    return;
  }

  fitCanvasToVideo(prevCvs, W, H);
  pCtx.drawImage(rawCvs, 0, 0);  // ใช้ภาพ raw ที่ไม่มีเส้นแดง
  const px900 = Math.round(H * LINE_TOP);
  const px100 = Math.round(H * LINE_BOT);

  const detected = findWaterLine(W, H, px900, px100);

  if (detected !== null) {
    pCtx.strokeStyle = '#00ff88';
    pCtx.lineWidth   = Math.max(6, Math.round(W * 0.012));
    pCtx.beginPath();
    pCtx.moveTo(0, detected);
    pCtx.lineTo(W, detected);
    pCtx.stroke();

    const raw    = 100 + ((px100 - detected) / (px100 - px900) * 800);
    const volume = Math.round(Math.max(0, Math.min(1000, raw)));
    showResult(volume + ' ml');
  } else {
    showError('หาผิวน้ำไม่เจอ\nลองขยับให้ขีด 900 ตรงเส้นแดงบน\nและให้แสงสว่างพอ');
  }

  liveCvs.style.display  = 'none';
  prevCvs.style.display   = 'block';
  snapBtn.style.display   = 'none';
  retakeBtn.style.display = 'block';
});

retakeBtn.addEventListener('click', () => {
  liveCvs.style.display   = 'block';
  prevCvs.style.display   = 'none';
  snapBtn.style.display   = 'block';
  retakeBtn.style.display  = 'none';
  resultEl.style.display   = 'none';
  errorEl.style.display    = 'none';
});

function findWaterLine(W, H, px900, px100) {
  const margin = 80;
  const top    = Math.max(0, px900 - margin);
  const bot    = Math.min(H - 1, px100 + margin);
  const stripH = bot - top;

  if (stripH <= 0) return null;

  const imgData = rCtx.getImageData(0, top, W, stripH);
  const d = imgData.data;
  const scores = new Float32Array(stripH);
  const step = Math.max(1, Math.floor(W / 100));

  for (let y = 1; y < stripH - 1; y++) {
    let s = 0;
    for (let x = 0; x < W; x += step) {
      const ic = (y * W + x) * 4;
      const iu = ((y - 1) * W + x) * 4;
      const id = ((y + 1) * W + x) * 4;

      const bc = (d[ic] + d[ic + 1] + d[ic + 2]) / 3;
      const bu = (d[iu] + d[iu + 1] + d[iu + 2]) / 3;
      const bd = (d[id] + d[id + 1] + d[id + 2]) / 3;

      s += Math.abs(bc - bu) + Math.abs(bc - bd);
    }
    scores[y] = s;
  }

  let best = -1;
  let bestScore = 0;

  for (let y = 2; y < stripH - 2; y++) {
    if (scores[y] > bestScore) {
      bestScore = scores[y];
      best = y;
    }
  }

  const mean = scores.reduce((a, b) => a + b, 0) / stripH;
  if (best === -1 || bestScore < mean * 2.0) return null;

  return top + best;
}

function showResult(text) {
  resultEl.textContent = text;
  resultEl.style.display = 'block';
  errorEl.style.display = 'none';
}

function showError(text) {
  errorEl.textContent = '❌ ' + text;
  errorEl.style.display = 'block';
  resultEl.style.display = 'none';
}
</script>
</body>
</html>
