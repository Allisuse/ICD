import streamlit as st
import cv2
import numpy as np
from PIL import Image
import streamlit.components.v1 as components

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="ICD Live Detector", layout="centered")

# ปรับแต่ง CSS พื้นหลัง
st.markdown("""
<style>
    .main { background: #0a0a1a; }
    div[data-testid="stCameraInput"] { margin-top: -30px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: #00f2fe;'>💧 เล็งขีดขวดให้ตรงเส้นแดงขณะถ่าย</h3>", unsafe_allow_html=True)

# ---- 1. LIVE CAMERA OVERLAY (ส่วนที่ทำให้เห็นเส้นบนมือถือ) ----
# ใช้ JavaScript เพื่อเปิดกล้องหลัง (environment) และวาดเส้นทับ
camera_html = """
<div style="position:relative; width:100%; max-width:480px; margin:0 auto;">
    <video id="video" autoplay playsinline muted 
           style="width:100%; border-radius:12px; display:block; background:#000;"></video>
    <canvas id="overlay" 
            style="position:absolute; top:0; left:0; width:100%; height:100%; 
                   pointer-events:none;"></canvas>
</div>

<script>
const video = document.getElementById('video');
const overlay = document.getElementById('overlay');
const ctx = overlay.getContext('2d');

// ตั้งค่าตำแหน่งเส้น (0.38 = 38% จากด้านบน, 0.62 = 62% จากด้านบน)
const LINE_TOP_PCT = 0.38;
const LINE_BOT_PCT = 0.62;

// ขอสิทธิ์เปิดกล้องหลัง
navigator.mediaDevices.getUserMedia({ 
    video: { facingMode: 'environment' }, 
    audio: false 
})
.then(stream => { video.srcObject = stream; })
.catch(err => { alert('ไม่สามารถเปิดกล้องได้: ' + err); });

function draw() {
    overlay.width = video.clientWidth;
    overlay.height = video.clientHeight;
    const H = overlay.height;
    const W = overlay.width;

    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = '#ff0000';
    ctx.lineWidth = 4;
    ctx.setLineDash([5, 5]); // เส้นประเพื่อให้มองเห็นผิวน้ำง่ายขึ้น

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

    ctx.setLineDash([]);
    ctx.fillStyle = '#ff0000';
    ctx.font = 'bold 16px Arial';
    ctx.fillText('900 ml', 10, (H * LINE_TOP_PCT) - 10);
    ctx.fillText('100 ml', 10, (H * LINE_BOT_PCT) - 10);

    requestAnimationFrame(draw);
}
video.addEventListener('play', draw);
</script>
"""

# แสดงหน้าจอกล้องจำลองพร้อมเส้นไกด์
components.html(camera_html, height=400)

st.write("---")

# ---- 2. ส่วนการถ่ายภาพและวิเคราะห์ (Capture & Analysis) ----
# เนื่องจาก Streamlit ยังไม่รองรับการดึงภาพจาก HTML Component โดยตรง 
# เรายังคงใช้ camera_input มาตรฐานในการรับรูปเพื่อประมวลผล OpenCV
img_file = st.camera_input("กดปุ่ม Take Photo ด้านล่างเพื่อวิเคราะห์")

if img_file:
    # โหลดภาพและเตรียม OpenCV
    img = cv2.cvtColor(np.array(Image.open(img_file)), cv2.COLOR_RGB2BGR)
    output = img.copy()
    h, w = img.shape[:2]

    # กำหนดตำแหน่งพิกเซลตามสัดส่วนเดียวกับเส้นไกด์ด้านบน
    px_900 = int(h * 0.38)
    px_100 = int(h * 0.62)

    # แสดงเส้นแดงบนรูปที่ถ่ายได้
    cv2.line(output, (0, px_900), (w, px_900), (0, 0, 255), 5)
    cv2.line(output, (0, px_100), (w, px_100), (0, 0, 255), 5)

    # อัลกอริทึมหาผิวน้ำ
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    edged = cv2.Canny(blurred, 30, 100)
    lines = cv2.HoughLinesP(edged, 1, np.pi/180, 35, minLineLength=40, maxLineGap=25)

    detected_y = None
    if lines is not None:
        lines = sorted(lines, key=lambda l: l[0][1])
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 10 and (px_900 - 50) < y1 < (px_100 + 50):
                detected_y = y1
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 10)
                break

    if detected_y:
        volume = 100 + ((px_100 - detected_y) / (px_100 - px_900) * 800)
        st.markdown(f"<h1 style='text-align:center; color:#00ff00;'>{int(volume)} ml</h1>", unsafe_allow_html=True)
    else:
        st.error("❌ หาผิวน้ำไม่เจอ — ลองเช็ดขวดให้แห้งและเล็งให้ตรงเส้นแดง")

    st.image(output, channels="BGR", use_container_width=True)
