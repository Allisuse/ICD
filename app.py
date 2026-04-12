import streamlit as st
import cv2
import numpy as np
from PIL import Image

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="ICD Align", layout="centered")

# ปรับ CSS เพื่อลดช่องว่างระหว่างรูป Guide และกล้อง ให้ขยับมาติดกันที่สุด
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    div[data-testid="stImage"] { margin-bottom: -50px; }
    div[data-testid="stCameraInput"] { margin-top: -20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: #00f2fe; font-size: 20px;'>💧 เล็งขีดขวดให้ตรงเส้นแดง</h3>", unsafe_allow_html=True)

# --- ส่วนการเล็ง (Alignment Zone) ---
# แสดงรูป Guide โดยบีบขนาดให้เล็กลงเพื่อไม่ให้ดันกล้องตกขอบจอ
try:
    guide_img = Image.open('guide_frame.png')
    st.image(guide_img, use_container_width=True)
except:
    st.error("ไม่พบไฟล์ Guide")

# วางกล้องต่อท้ายทันที
img_file = st.camera_input("แสกนขวดตรงนี้")

# --- ส่วนการประมวลผล ---
if img_file is not None:
    image = Image.open(img_file)
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    output = img.copy()
    
    px_900, px_100 = 1107, 1471
    
    # วาดเส้นแดงเช็กตำแหน่งในรูปที่ถ่ายได้
    cv2.line(output, (0, px_900), (img.shape[1], px_900), (0, 0, 255), 8)
    cv2.line(output, (0, px_100), (img.shape[1], px_100), (0, 0, 255), 8)

    # ค้นหาระดับน้ำ
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(cv2.GaussianBlur(gray, (7,7), 0), 40, 120)
    lines = cv2.HoughLinesP(edged, 1, np.pi/180, 60, minLineLength=100, maxLineGap=10)

    detected_y = None
    if lines is not None:
        lines = sorted(lines, key=lambda l: l[0][1], reverse=True)
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 5 and px_900 < y1 < px_100:
                detected_y = y1
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 12)
                break

    # แสดงผล
    if detected_y:
        volume = 100 + ((px_100 - detected_y) / (px_100 - px_900) * 800)
        st.markdown(f"<h2 style='text-align: center; color: #00ff00;'>{int(volume)} ml</h2>", unsafe_allow_html=True)
    else:
        st.error("หาผิวน้ำไม่เจอ")

    st.image(output, channels="BGR", use_container_width=True)
