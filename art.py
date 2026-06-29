import cv2
import mediapipe as mp
import numpy as np
import math

# ================= INIT =================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# ================= VARIABLES =================
canvas = None
prev_x, prev_y = 0, 0
drawing_color = (0, 255, 255)
thickness = 5
prev_dist = None

# ================= FUNCTIONS =================
def finger_up(h, tip, pip):
    return h.landmark[tip].y < h.landmark[pip].y

def pinch(h, W, H):
    x1, y1 = h.landmark[4].x*W, h.landmark[4].y*H
    x2, y2 = h.landmark[8].x*W, h.landmark[8].y*H
    return math.hypot(x2-x1, y2-y1) < 40

# ================= MAIN LOOP =================
while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    H, W, _ = frame.shape

    if canvas is None:
        canvas = np.zeros_like(frame)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    if res.multi_hand_landmarks:
        h1 = res.multi_hand_landmarks[0]

        x, y = int(h1.landmark[8].x * W), int(h1.landmark[8].y * H)

        # ===== TWO HANDS FOR THICKNESS =====
        if len(res.multi_hand_landmarks) == 2:
            h2 = res.multi_hand_landmarks[1]
            c1 = (h1.landmark[8].x*W, h1.landmark[8].y*H)
            c2 = (h2.landmark[8].x*W, h2.landmark[8].y*H)
            dist = math.hypot(c2[0]-c1[0], c2[1]-c1[1])
            if prev_dist:
                thickness = int(np.interp(dist,[50,300],[1,20]))
            prev_dist = dist
        else:
            prev_dist = None

        # ===== PINCH TO CLEAR =====
        if pinch(h1, W, H):
            canvas = np.zeros_like(frame)
            prev_x, prev_y = 0, 0
        else:
            # ===== DRAWING TELUNJUK UP =====
            if finger_up(h1,8,6):
                if prev_x == 0 and prev_y == 0:
                    prev_x, prev_y = x, y
                cv2.line(canvas, (prev_x, prev_y), (x, y), drawing_color, thickness)
                prev_x, prev_y = x, y
            else:
                prev_x, prev_y = 0, 0

        # ===== OPTIONAL: CHANGE COLOR =====
        # Jika telunjuk + tengah up → merah
        if finger_up(h1,8,6) and finger_up(h1,12,10):
            drawing_color = (0,0,255)
        # Jika telunjuk + kelingking up → hijau
        elif finger_up(h1,8,6) and finger_up(h1,20,18):
            drawing_color = (0,255,0)
        # Jika hanya telunjuk → kuning
        elif finger_up(h1,8,6):
            drawing_color = (0,255,255)

        # gambar titik jari
        cv2.circle(frame, (x, y), 8, drawing_color, -1)

    # gabung canvas dan frame
    frame = cv2.addWeighted(frame, 0.5, canvas, 0.5, 0)

    cv2.putText(frame, "Pinch jari untuk CLEAR | Angkat jari aman", (10,40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.putText(frame, f"Thickness: {thickness}", (10,70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)
    cv2.putText(frame, f"Color: {drawing_color}", (10,100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

    cv2.imshow("Hand Drawing PRO", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()