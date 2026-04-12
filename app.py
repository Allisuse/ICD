import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="ICD Detector", layout="centered")

st.markdown("<h2 style='text-align:center; color:#00d4ff;'>💧 ICD Volume Detector</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888;'>ถ่ายรูปด้วย <b>icd_camera.html</b> บนมือถือ แล้วอัปโหลดที่นี่</p>", unsafe_allow_html=True)

st.info("📱 บนมือถือ: เปิดไฟล์ icd_camera.html → ถ่ายรูป → Save → อัปโหลดด้านล่าง")

img_file = st.file_uploader("อัปโหลดรูปขวด", type=["jpg", "jpeg", "png"])

if img_file:
    img    = cv2.cvtColor(np.array(Image.open(img_file)), cv2.COLOR_RGB2BGR)
    output = img.copy()
    h, w   = img.shape[:2]

    px_900 = int(h * 0.35)
    px_100 = int(h * 0.65)

    cv2.line(output, (0, px_900), (w, px_900), (0, 0, 255), 5)
    cv2.line(output, (0, px_100), (w, px_100), (0, 0, 255), 5)

    gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    edged   = cv2.Canny(blurred, 30, 100)

    lines = cv2.HoughLinesP(edged, 1, np.pi/180,
                             threshold=35, minLineLength=40, maxLineGap=25)
    detected_y = None

    if lines is not None:
        search_min = px_900 - 80
        search_max = px_100 + 80
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
            f"<h1 style='text-align:center; color:#00ff88;'>{int(volume)} ml</h1>",
            unsafe_allow_html=True
        )
    else:
        st.error("❌ หาผิวน้ำไม่เจอ — ลองถ่ายใหม่ให้แสงสว่างพอ")

    st.image(output, channels="BGR", use_container_width=True)
