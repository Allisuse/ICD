Live camera

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import streamlit.components.v1 as components

st.set_page_config(page_title="ICD Detector", layout="centered")

st.markdown("""
<style>
    .main { background: #0a0a1a; }
    h3 { font-family: 'Segoe UI', sans-serif; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: #00f2fe;'>💧 เล็งขีดขวดให้ตรงเส้นแดง</h3>", unsafe_allow_html=True)

# ---- LIVE CAMERA WITH CANVAS OVERLAY ----
# This HTML+JS component shows live camera with red guide lines drawn on top via canvas
# Two horizontal red lines at 35% and 65% of video height (adjust LINE_TOP_PCT / LINE_BOT_PCT as needed)
camera_html = """
<div style="position:relative; width:100%; max-width:480px; margin:0 auto;">
  <video id="video" autoplay playsinline muted
         style="width:100%; border-radius:12px; display:block;"></video>
  <canvas id="overlay"
          style="position:absolute; top:0; left:0; width:100%; height:100%;
                 border-radius:12px; pointer-events:none;"></canvas>
  <div style="text-align:center; margin-top:8px;">
    <button id="snapBtn"
            style="background:#00f2fe; color:#000; border:none; padding:10px 28px;
                   border-radius:8px; font-size:16px; font-weight:bold; cursor:pointer;">
      📸 ถ่ายรูป
    </button>
  </div>
  <canvas id="snapCanvas" style="display:none;"></canvas>
  <div id="snapResult" style="text-align:center; margin-top:8px;"></div>
</div>

<script>
const LINE_TOP_PCT = 0.38;   // position of 900ml line  (0 = top, 1 = bottom)
const LINE_BOT_PCT = 0.62;   // position of 100ml line

const video   = document.getElementById('video');
const overlay = document.getElementById('overlay');
const ctx     = overlay.getContext('2d');

// Start camera
navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false })
  .then(stream => { video.srcObject = stream; })
  .catch(err => { console.error('Camera error:', err); });

// Resize overlay canvas to match video each frame
function drawLines() {
  const W = video.videoWidth  || video.clientWidth;
  const H = video.videoHeight || video.clientHeight;
  overlay.width  = W;
  overlay.height = H;

  const y900 = Math.round(H * LINE_TOP_PCT);
  const y100 = Math.round(H * LINE_BOT_PCT);

  ctx.clearRect(0, 0, W, H);

  // Shadow glow effect
  ctx.shadowColor = 'rgba(255,0,0,0.8)';
  ctx.shadowBlur  = 10;
  ctx.strokeStyle = '#ff2222';
  ctx.lineWidth   = 4;

  // Top line (900 ml)
  ctx.beginPath(); ctx.moveTo(0, y900); ctx.lineTo(W, y900); ctx.stroke();
  // Bottom line (100 ml)
  ctx.beginPath(); ctx.moveTo(0, y100); ctx.lineTo(W, y100); ctx.stroke();

  // Labels
  ctx.shadowBlur = 0;
  ctx.fillStyle  = '#ff2222';
  ctx.font       = 'bold 18px Segoe UI, sans-serif';
  ctx.fillText('─ 900 ml', 8, y900 - 6);
  ctx.fillText('─ 100 ml', 8, y100 - 6);

  requestAnimationFrame(drawLines);
}
video.addEventListener('loadedmetadata', drawLines);
// Fallback if loadedmetadata already fired
if (video.readyState >= 1) drawLines();
</script>
"""

components.html(camera_html, height=520)

st.markdown("---")
st.markdown("<h4 style='color:#aaa;'>หรือถ่ายรูปเพื่อวิเคราะห์ปริมาตร</h4>", unsafe_allow_html=True)

# ---- PHOTO CAPTURE + ANALYSIS (unchanged logic) ----
img_file = st.camera_input("ถ่ายรูปขวดเพื่อวิเคราะห์")

if img_file:
    img    = cv2.cvtColor(np.array(Image.open(img_file)), cv2.COLOR_RGB2BGR)
    output = img.copy()
    h, w   = img.shape[:2]

    # Guide lines at same relative positions as the live overlay
    px_900 = int(h * 0.38)
    px_100 = int(h * 0.62)

    cv2.line(output, (0, px_900), (w, px_900), (0, 0, 255), 5)
    cv2.line(output, (0, px_100), (w, px_100), (0, 0, 255), 5)

    # Edge detection
    gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    edged   = cv2.Canny(blurred, 30, 100)

    lines = cv2.HoughLinesP(edged, 1, np.pi/180,
                             threshold=35, minLineLength=40, maxLineGap=25)
    detected_y = None

    if lines is not None:
        search_min = px_900 - 60
        search_max = px_100 + 60
        lines = sorted(lines, key=lambda l: l[0][1])
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 8 and search_min < y1 < search_max:
                detected_y = y1
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 10)
                break

    if detected_y:
        volume = 100 + ((px_100 - detected_y) / (px_100 - px_900) * 800)
        st.markdown(
            f"<h1 style='text-align:center; color:#00ff00;'>{int(volume)} ml</h1>",
            unsafe_allow_html=True
        )
    else:
        st.error("❌ หาผิวน้ำไม่เจอ — ลองขยับให้ขีด 900 ตรงกับเส้นแดงบน")

    st.image(output, channels="BGR", use_container_width=True)
