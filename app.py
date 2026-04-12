import streamlit as st
import cv2
import numpy as np
from PIL import Image
import streamlit.components.v1 as components

st.set_page_config(page_title="ICD Live Detector", layout="centered")

# ปรับ CSS ให้เหมาะกับหน้าจอมือถือ
st.markdown("""
<style>
    .main { background: #0a0a1a; }
    /* ลดช่องว่างเพื่อให้องค์ประกอบเบียดกันในหน้าเดียว */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    iframe { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: #00f2fe;'>💧 เล็งขีดขวดให้ตรงเส้นแดง</h3>", unsafe_allow_html=True)

# ---- 1. LIVE CAMERA OVERLAY (ปรับปรุงเพื่อมือถือ) ----
camera_html = """
<div style="position:relative; width:100%; max-width:480px; margin:0 auto; overflow:hidden;">
    <video id="video" autoplay playsinline muted 
           style="width:100%; border-radius:12px; display:block; background:#000; transform: scaleX(1);"></video>
    <canvas id="overlay" 
            style="position:absolute; top:0; left:0; width:100%; height:100%; 
                   pointer-events:none;"></canvas>
</div>

<script>
const video = document.getElementById('video');
const overlay = document.getElementById('overlay');
const ctx = overlay.getContext('2d');

const LINE_TOP_PCT = 0.38; 
const LINE_BOT_PCT = 0.62;

// ตั้งค่าขอใช้กล้องหลัง (Environment) สำหรับมือถือ
const constraints = {
    video: { 
        facingMode: { exact: "environment" },
        width: { ideal: 1280 },
        height: { ideal: 720 }
    },
    audio: false
};

// ถ้าเป็น Browser ในคอมอาจไม่มีกล้องหลัง ให้ลองขอแบบทั่วไปถ้าแบบ exact พลาด
navigator.mediaDevices.getUserMedia(constraints)
    .then(stream => { video.srcObject = stream; })
    .catch(err => {
        console.log("พยายามเปิดกล้องหลังแบบทั่วไป...");
        navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
            .then(stream => { video.srcObject = stream; })
            .catch(e => alert("ไม่สามารถเข้าถึงกล้องได้: " + e));
    });

function drawLines() {
    overlay.width = video.clientWidth;
    overlay.height = video.clientHeight;
    const W = overlay.width;
    const H = overlay.height;

    ctx.clearRect(0, 0, W, H);
    
    // ตั้งค่าเส้นแดงแบบเรืองแสง (Glow Effect) เพื่อให้มองชัดในที่มืด
    ctx.shadowColor = 'red';
    ctx.shadowBlur = 15;
    ctx.strokeStyle = '#ff0000';
    ctx.lineWidth = 4;
    ctx.setLineDash([10, 10]); 

    // วาดเส้น 900ml
    ctx.beginPath();
    ctx.moveTo(0, H * LINE_TOP_PCT);
    ctx.lineTo(W, H * LINE_TOP_PCT);
    ctx.stroke();

    // วาดเส้น 100ml
    ctx.beginPath();
    ctx.moveTo(0, H * LINE_BOT_PCT);
    ctx.lineTo(W, H * LINE_BOT_PCT);
    ctx.stroke();

    ctx.shadowBlur = 0;
    ctx.setLineDash([]);
    ctx.fillStyle = '#ff0000';
    ctx.font = 'bold 18px sans-serif';
    ctx.fillText('─ 900 ml', 10, (H * LINE_TOP_PCT) - 10);
    ctx.fillText('─ 100 ml', 10, (H * LINE_BOT_PCT) - 10);

    requestAnimationFrame(drawLines);
}
video.addEventListener('play', drawLines);
</script>
"""

# แสดงหน้าจอกล้องสดพร้อมเส้นไกด์ (ความสูง 420 กำลังพอดีกับ iPhone/Android)
components.html(camera_html, height=420)

st.write("---")

# ---- 2. ส่วนการถ่ายภาพเพื่อคำนวณ ----
img_file = st.camera_input("📸 กดถ่ายภาพเพื่อวิเคราะห์ปริมาตร")

if img_file:
    # กระบวนการ OpenCV เดิมที่แม่นยำของคุณ
    img = cv2.cvtColor(np.array(Image.open(img_file)), cv2.COLOR_RGB2BGR)
    output = img.copy()
    h, w = img.shape[:2]

    px_900 = int(h * 0.38)
    px_100 = int(h * 0.62)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    edged = cv2.Canny(blurred, 30, 100)
    lines = cv2.HoughLinesP(edged, 1, np.pi/180, 35, minLineLength=40, maxLineGap=25)

    detected_y = None
    if lines is not None:
        lines = sorted(lines, key=lambda l: l[0][1])
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 10 and (px_900 - 60) < y1 < (px_100 + 60):
                detected_y = y1
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 12)
                break

    if detected_y:
        volume = 100 + ((px_100 - detected_y) / (px_100 - px_900) * 800)
        st.markdown(f"<h1 style='text-align:center; color:#00ff00;'>{int(volume)} ml</h1>", unsafe_allow_html=True)
    else:
        st.error("หาผิวน้ำไม่เจอ — ลองเล็งให้ขีด 900 ตรงกับเส้นแดงในกล้องด้านบน")
    
    # วาดเส้นไกด์แดงทับรูปผลลัพธ์เพื่อเช็คการเล็ง
    cv2.line(output, (0, px_900), (w, px_900), (0, 0, 255), 5)
    cv2.line(output, (0, px_100), (w, px_100), (0, 0, 255), 5)
    st.image(output, channels="BGR", use_container_width=True)
