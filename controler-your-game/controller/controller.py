import cv2
import mediapipe as mp
import pyautogui
import time

pyautogui.PAUSE = 0

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# turunkan resolusi kamera biar ringan
cap.set(3, 640)
cap.set(4, 480)

last_action = 0
cooldown = 0.3


def count_fingers(hand_landmarks, h, w):
    fingers = []

    tips = [8, 12, 16, 20]

    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers.count(1)


while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            total_fingers = count_fingers(hand_landmarks, h, w)

            cv2.putText(frame, f"Fingers: {total_fingers}", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

            now = time.time()

            if now - last_action > cooldown:

                if total_fingers == 1:
                    pyautogui.press("right")
                    last_action = now

                elif total_fingers == 2:
                    pyautogui.press("left")
                    last_action = now

                elif total_fingers == 3:
                    pyautogui.press("up")
                    last_action = now

                elif total_fingers == 4:
                    pyautogui.press("down")
                    last_action = now

    cv2.imshow("Hand Gesture Controller - Subway Surfers", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()