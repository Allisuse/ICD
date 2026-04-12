import streamlit as st
import cv2
import numpy as np
from PIL import Image

# ตั้งค่าหน้าจอแบบมาตรฐานเพื่อให้องค์ประกอบอยู่ตรงกลาง
st.set_page_config(page_title="ICD Volume Detector", layout="centered")

# ส่วนหัวแอป
st.markdown("<h2 style='text-align: center; color: #00f2fe;'>💧 เล็งขีดขวดให้ตรงกับเส้นสีแดง</h2>", unsafe_allow_html=True)

# --- ส่วนที่ 1: การแสดงผลเพื่อการเล็ง (Alignment Zone) ---
# วางรูป Guide ไว้ด้านบนสุดเพื่อเป็นบรรทัดฐาน
try:
    guide_img = Image.open('guide_frame.png')
    st.image(guide_img, caption="ขีด 900 (บน) | ขีด 100 (ล่าง)", use_container_width=True)
except:
    st.error("ไม่พบไฟล์ guide_frame.png")

# วางกล้องไว้ต่อจากรูป Guide ทันทีเพื่อให้ตาเราเทียบตำแหน่งเดิมได้ง่าย
img_file = st.camera_input("สแกนขวดน้ำเกลือตรงนี้")

# --- ส่วนที่ 2: การประมวลผลหลังถ่ายรูป ---
if img_file is not None:
    st.write("---")
    
    # แปลงภาพ
    image = Image.open(img_file)
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    output = img.copy()
    
    # ค่าพิกเซลเดิมที่คุณตั้งไว้
    px_900 = 1107
    px_100 = 1471
    
    # วาดเส้นไกด์ (สีแดง) ลงบนรูปที่ถ่ายได้ทันที เพื่อเช็คว่าเล็งพลาดไหม
    cv2.line(output, (0, px_900), (img.shape[1], px_900), (0, 0, 255), 8) # เส้น 900
    cv2.line(output, (0, px_100), (img.shape[1], px_100), (0, 0, 255), 8) # เส้น 100

    # ประมวลผลหาผิวน้ำ
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    edged = cv2.Canny(blurred, 40, 120)
    lines = cv2.HoughLinesP(edged, 1, np.pi/180, 60, minLineLength=100, maxLineGap=10)

    detected_y = None
    if lines is not None:
        lines = sorted(lines, key=lambda l: l[0][1], reverse=True)
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 5 and px_900 < y1 < px_100:
                detected_y = y1
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 12) # เส้นเขียวที่ผิวน้ำ
                break

    # แสดงผลลัพธ์
    if detected_y:
        volume = 100 + ((px_100 - detected_y) / (px_100 - px_900) * 800)
        st.markdown(f"<h1 style='text-align: center; color: #00ff00;'>{int(volume)} ml</h1>", unsafe_allow_html=True)
        cv2.putText(output, f"{int(volume)} ml", (50, 250), cv2.FONT_HERSHEY_DUPLEX, 5, (0, 255, 255), 10)
    else:
        st.error("❌ หาผิวน้ำไม่พบ กรุณาเล็งให้ขีดตรงกับเส้นแดงในรูป Guide")

    # แสดงรูปวิเคราะห์ขนาดใหญ่
    st.image(output, channels="BGR", use_container_width=True)
