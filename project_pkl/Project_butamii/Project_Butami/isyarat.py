import cv2
import mediapipe as mp
import pyttsx3

# Inisialisasi MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Inisialisasi TTS
engine = pyttsx3.init()
engine.setProperty("rate", 150)  # kecepatan bicara
engine.setProperty("volume", 1.0)  # volume max

last_spoken = ""  # untuk menghindari suara diulang terus

# Fungsi untuk menghitung jari yang terangkat
def count_fingers(hand_landmarks):
    finger_tips = [8, 12, 16, 20]   # ujung telunjuk, tengah, manis, kelingking
    finger_pip = [6, 10, 14, 18]    # sendi PIP jari

    count = 0
    for tip, pip in zip(finger_tips, finger_pip):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            count += 1

    # Deteksi jempol
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        count += 1

    return count

# Mapping gesture ke teks
def detect_gesture(hand_landmarks):
    finger_count = count_fingers(hand_landmarks)

    if finger_count == 1:
        return "Perkenalkan"
    elif finger_count == 2:
        return "Nama saya Ainun"
    elif finger_count == 3:
        return "Terima kasih"
    else:
        # Metal 🤘 (telunjuk & kelingking naik, yang lain turun)
        index_up = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
        pinky_up = hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y
        middle_down = hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y
        ring_down = hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y

        if index_up and pinky_up and middle_down and ring_down:
            return "Metal"

        # Telepon 🤙 (jempol + kelingking naik, jari lain turun)
        thumb_open = hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x
        index_down = hand_landmarks.landmark[8].y > hand_landmarks.landmark[6].y
        middle_down = hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y
        ring_down = hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y

        if thumb_open and pinky_up and index_down and middle_down and ring_down:
            return "Telepon saya"

    return None

# Kamera real-time
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    image = cv2.flip(image, 1)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_image)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            gesture = detect_gesture(hand_landmarks)
            if gesture:
                cv2.putText(image, gesture, (50, 100), cv2.FONT_HERSHEY_SIMPLEX,
                            1.2, (0, 255, 0), 3, cv2.LINE_AA)

                # Biar suara ga spam, cek dulu apakah gesture berubah
                if gesture != last_spoken:
                    engine.say(gesture)
                    engine.runAndWait()
                    last_spoken = gesture

    cv2.imshow("Bahasa Isyarat", image)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC untuk keluar
        break

cap.release()
cv2.destroyAllWindows()
