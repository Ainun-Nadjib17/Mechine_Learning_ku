import cv2
import mediapipe as mp
import numpy as np
import joblib
from collections import deque
from statistics import mode, StatisticsError

# ==========================
# 1. LOAD MODEL & SCALER
# ==========================
print("Loading model...")
model = joblib.load("alphabet_model.pkl")
scaler = joblib.load("alphabet_scaler.pkl")
le = joblib.load("alphabet_label_encoder.pkl")
print("Model berhasil dimuat!")

# ==========================
# 2. MEDIAPIPE SETUP
# ==========================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,       # Dataset kita 2 tangan (126 fitur)
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ==========================
# 3. WEBCAM & BUFFER
# ==========================
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Tidak bisa mengakses kamera!")
    exit()

# Buffer untuk smoothing (mencegah huruf berkedip-kedip)
prediction_buffer = deque(maxlen=10) 
current_prediction = "-"

while True:
    success, frame = cap.read()
    if not success:
        break

    # Flip frame agar seperti cermin (lebih natural)
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        features = []
        detected_hands = results.multi_hand_landmarks

        # Ambil maksimal 2 tangan
        for hand_landmarks in detected_hands[:2]:
            # Gambar skeleton tangan di layar
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Ekstrak koordinat x, y, z
            for lm in hand_landmarks.landmark:
                features.extend([lm.x, lm.y, lm.z])

        # PENTING: Dataset kita 126 fitur (2 tangan). 
        # Jika di webcam cuma terdeteksi 1 tangan, isi sisanya dengan 0.
        while len(features) < 126:
            features.append(0.0)
        
        # Potong jika kelebihan (jaga-jaga)
        features = features[:126]

        features = np.array(features).reshape(1, -1)

        # 1. Scaling fitur (WAJIB, karena saat training di-scaling)
        features_scaled = scaler.transform(features)

        # 2. Prediksi & Confidence Score
        probabilities = model.predict_proba(features_scaled)[0]
        pred_idx = np.argmax(probabilities)
        confidence = np.max(probabilities) * 100
        
        # Ambil label asli dari LabelEncoder
        pred_label = le.inverse_transform([pred_idx])[0]
        
        # Konversi angka (0-25) ke huruf (A-Z) jika label aslinya berupa angka
        if str(pred_label).isdigit():
            pred_letter = chr(int(pred_label) + 65) # 65 adalah ASCII untuk 'A'
        else:
            pred_letter = str(pred_label)
        
        # 3. Smoothing (Masukkan ke buffer dan ambil modus)
        prediction_buffer.append(pred_letter)
        try:
            current_prediction = mode(prediction_buffer)
        except StatisticsError:
            current_prediction = prediction_buffer[-1]

        # Tampilkan Huruf & Confidence di layar
        # Warna hijau jika yakin > 85%, orange jika ragu
        color = (0, 255, 0) if confidence > 85 else (0, 165, 255) 
        
        cv2.putText(frame, f"Letter: {current_prediction}", (20, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, color, 3)
        cv2.putText(frame, f"Conf: {confidence:.1f}%", (20, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    else:
        # Reset buffer jika tidak ada tangan
        prediction_buffer.clear()
        current_prediction = "-"
        cv2.putText(frame, "Letter: -", (20, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

    # Instruksi di pojok kiri bawah
    cv2.putText(frame, "Press ESC to Exit", (20, frame.shape[0] - 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Tampilkan window
    cv2.imshow("BISINDO Alphabet Recognition", frame)

    # Tekan ESC untuk keluar
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()