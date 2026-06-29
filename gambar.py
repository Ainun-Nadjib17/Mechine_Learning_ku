import cv2
import mediapipe as mp
import numpy as np
import math
import time

# ================= INIT =================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

canvas = None
color = (255, 0, 0)
colors = [(255,0,0), (0,255,0), (0,0,255), (0,255,255), (255,0,255)]
color_index = 0

prev_x, prev_y = 0, 0
save_cooldown = 0

# ================= FUNCTION =================
def count_fingers(hand_landmarks):
    tips = [8, 12, 16, 20]
    count = 0
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            count += 1
    return count

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)

    if canvas is None:
        canvas = np.zeros_like(frame)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            h, w, c = frame.shape

            lm_list = []
            for id, lm in enumerate(handLms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((id, cx, cy))

            fingers = count_fingers(handLms)

            # Telunjuk
            x1, y1 = lm_list[8][1], lm_list[8][2]

            # ================= DRAW MODE =================
            if fingers == 1:
                if prev_x == 0 and prev_y == 0:
                    prev_x, prev_y = x1, y1

                cv2.line(canvas, (prev_x, prev_y), (x1, y1), color, 5)
                prev_x, prev_y = x1, y1
            else:
                prev_x, prev_y = 0, 0

            # ================= CHANGE COLOR =================
            if fingers == 2:
                color_index = (color_index + 1) % len(colors)
                color = colors[color_index]
                time.sleep(0.3)

            # ================= CLEAR =================
            if fingers == 4:
                canvas = np.zeros_like(frame)
                time.sleep(0.5)

            # ================= SAVE =================
            x_thumb, y_thumb = lm_list[4][1], lm_list[4][2]
            distance = math.hypot(x_thumb - x1, y_thumb - y1)

            if distance < 30 and time.time() - save_cooldown > 2:
                cv2.imwrite("air_drawing.png", canvas)
                print("Gambar Disimpan!")
                save_cooldown = time.time()

            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

    # Gabungkan canvas dan frame
    combined = cv2.add(frame, canvas)

    cv2.imshow("Air Drawing Pro", combined)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()