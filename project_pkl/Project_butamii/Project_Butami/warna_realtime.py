import cv2
import numpy as np

# === Variabel global ===
clicked = False
r = g = b = xpos = ypos = 0

# Fungsi event untuk klik mouse
def pick_color(event, x, y, flags, param):
    global clicked, r, g, b, xpos, ypos
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked = True
        xpos, ypos = x, y
        b, g, r = frame[y, x]
        b, g, r = int(b), int(g), int(r)

# Buka kamera
cap = cv2.VideoCapture(0)
cv2.namedWindow("Kamera")
cv2.setMouseCallback("Kamera", pick_color)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Kalau ada warna yang diklik
    if clicked:
        # Kotak warna
        color_preview = np.zeros((100, 300, 3), np.uint8)
        color_preview[:] = [b, g, r]

        # Teks RGB
        text = f"RGB: ({r}, {g}, {b})"
        cv2.putText(color_preview, text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255-r, 255-g, 255-b), 2, cv2.LINE_AA)

        cv2.imshow("Picked Color", color_preview)

    # Tampilkan kamera
    cv2.imshow("Kamera", frame)

    # Tekan ESC untuk keluar
    if cv2.waitKey(20) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
