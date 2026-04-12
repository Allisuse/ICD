import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="ICD Detector", layout="centered")

# ปรับให้ส่วนประกอบชิดกัน
st.markdown("<style>div[data-testid='stImage'] { margin-bottom: -60px; } </style>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #00f2fe;'>💧 เล็งขีดขวดให้ตรงเส้นแดง</h3>", unsafe_allow_html=True)

# 1. แสดงรูป Guide
try:
    st.image('guide_frame.png', use_container_width=True)
except:
    st.info("ระบบพร้อมใช้งาน")

# 2. ส่วนถ่ายรูป
img_file = st.camera_input("สแกนขวดตรงนี้")

if img_file:
    img = cv2.cvtColor(np.array(Image.open(img_file)), cv2.COLOR_RGB2BGR)
    output = img.copy()
    
    # --- จุดที่ต้องเช็ค: พิกเซลเหล่านี้ต้องตรงกับตำแหน่งในรูปถ่ายจริง ---
    px_900, px_100 = 1107, 1471
    
    # วาดเส้นไกด์สีแดง
    cv2.line(output, (0, px_900), (img.shape[1], px_900), (0, 0, 255), 5)
    cv2.line(output, (0, px_100), (img.shape[1], px_100), (0, 0, 255), 5)

    # --- การประมวลผลที่ "หาเจอง่ายขึ้น" ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # เพิ่มความฟุ้งเพื่อให้เส้นแสงสะท้อนจางลง
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    # ปรับ Canny ให้จับเส้นขอบได้ไวขึ้น
    edged = cv2.Canny(blurred, 30, 100)
    
    # ปรับ HoughLines ให้หาเส้นเจอได้ง่ายขึ้นแม้เส้นจะไม่ยาวมาก
    lines = cv2.HoughLinesP(edged, 1, np.pi/180, threshold=35, minLineLength=40, maxLineGap=25)

    detected_y = None
    if lines is not None:
        # หาเส้นแนวนอนในช่วงพิกเซลที่เราสนใจ (เผื่อระยะให้กว้างขึ้น)
        search_min = px_900 - 50 
        search_max = px_100 + 50
        
        lines = sorted(lines, key=lambda l: l[0][1])
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # กรองเฉพาะเส้นที่ค่อนข้างเป็นแนวนอน
            if abs(y1 - y2) < 8 and search_min < y1 < search_max:
                detected_y = y1
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 10)
                break

    # 3. แสดงผล
    if detected_y:
        volume = 100 + ((px_100 - detected_y) / (px_100 - px_900) * 800)
        st.markdown(f"<h1 style='text-align: center; color: #00ff00;'>{int(volume)} ml</h1>", unsafe_allow_html=True)
    else:
        st.error("❌ หาผิวน้ำไม่เจอ: ลองขยับมือถือให้ขีด 900 บนขวดตรงกับเส้นแดงในภาพ")
    
    st.image(output, channels="BGR", use_container_width=True)
