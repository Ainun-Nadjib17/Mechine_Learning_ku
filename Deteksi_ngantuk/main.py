import cv2
import numpy as np
import mediapipe as mp
# FIX: Import langsung dari mediapipe.python.solutions
from mediapipe.python.solutions import face_mesh, drawing_utils, drawing_styles
import winsound
import time
import os
import wave
import struct
import math

# ============================================================
# KONFIGURASI
# ============================================================
EAR_THRESHOLD = 0.25        
FRAME_THRESHOLD = 20        
WARNING_WAV = "warning.wav" 

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# ============================================================
# INISIALISASI MEDIAPIPE
# ============================================================
face_mesh_model = face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

drawing = drawing_utils
mp_drawing_styles = drawing_styles

# FIX: Buat custom drawing spec untuk jaring wajah (Mesh) warna hijau neon
# thickness=1 biar garisnya tipis dan rapi, circle_radius=1 untuk titik landmark
mesh_drawing_spec = drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)

# ============================================================
# FUNGSI AUTO-GENERATE FILE SUARA (.WAV)
# ============================================================
def generate_warning_wav(filename="warning.wav"):
    print(f"🔊 File '{filename}' tidak ditemukan. Sedang membuat otomatis...")
    sample_rate = 44100
    duration = 1.5  
    frequency = 880.0  

    try:
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            for i in range(int(sample_rate * duration)):
                value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
                data = struct.pack('<h', value)
                wav_file.writeframes(data)
        print(f"✅ File '{filename}' berhasil dibuat otomatis!")
    except Exception as e:
        print(f"❌ Gagal membuat file suara: {e}")

def play_alarm():
    if not os.path.exists(WARNING_WAV):
        generate_warning_wav(WARNING_WAV)
    try:
        winsound.PlaySound(WARNING_WAV, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        winsound.Beep(1000, 500)

# ============================================================
# FUNGSI HITUNG EAR
# ============================================================
def calculate_ear(landmarks, eye_indices):
    points = [landmarks[i] for i in eye_indices]
    p2_p6 = np.linalg.norm(np.array([points[1].x, points[1].y]) - np.array([points[5].x, points[5].y]))
    p3_p5 = np.linalg.norm(np.array([points[2].x, points[2].y]) - np.array([points[4].x, points[4].y]))
    p1_p4 = np.linalg.norm(np.array([points[0].x, points[0].y]) - np.array([points[3].x, points[3].y]))

    if p1_p4 == 0: return 0.0
    return (p2_p6 + p3_p5) / (2.0 * p1_p4)

# ============================================================
# FUNGSI UTAMA
# ============================================================
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("🔴 Kamera tidak terbaca!")
        return

    print("DEBUG MODE: Kamera menyala...")
    print(f"EAR Threshold: {EAR_THRESHOLD} | Frame Threshold: {FRAME_THRESHOLD}")
    print("Tekan 'q' untuk keluar.\n")

    frame_counter = 0
    alarm_active = False
    last_alarm_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("🔴 Kamera tidak terbaca!")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh_model.process(rgb)
        h, w, _ = frame.shape

        if results.multi_face_landmarks:
            for face in results.multi_face_landmarks:
                
                # FIX: UBAH DISINI! Menggunakan FACEMESH_TESSELATION untuk jaring penuh
                drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face,
                    connections=face_mesh.FACEMESH_TESSELATION, # <-- Jaring penuh (Mesh)
                    landmark_drawing_spec=mesh_drawing_spec,    # <-- Titik hijau kecil
                    connection_drawing_spec=mesh_drawing_spec   # <-- Garis hijau tipis
                )

                landmarks = face.landmark
                left_ear = calculate_ear(landmarks, LEFT_EYE)
                right_ear = calculate_ear(landmarks, RIGHT_EYE)
                avg_ear = (left_ear + right_ear) / 2.0

                # Teks EAR
                cv2.putText(frame, f"EAR: {avg_ear:.3f}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                # Logika Deteksi Kantuk
                if avg_ear < EAR_THRESHOLD:
                    frame_counter += 1
                    if frame_counter >= FRAME_THRESHOLD:
                        cv2.putText(frame, "MATA TERTUTUP", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                        cv2.putText(frame, "ANDA MENGANTUK, SEGERA ISTIRAHAT", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                        current_time = time.time()
                        if not alarm_active or (current_time - last_alarm_time) > 3:
                            play_alarm()
                            alarm_active = True
                            last_alarm_time = current_time
                else:
                    frame_counter = 0
                    alarm_active = False

                # Highlight area mata (Opsional, biar lebih jelas area yang dideteksi)
                for eye_indices, color in [(LEFT_EYE, (0, 255, 255)), (RIGHT_EYE, (255, 0, 255))]:
                    eye_points = np.array([[int(landmarks[i].x * w), int(landmarks[i].y * h)] for i in eye_indices], np.int32)
                    cv2.polylines(frame, [eye_points], True, color, 2)
        else:
            cv2.putText(frame, "Wajah tidak terdeteksi", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        # Teks Frame Counter
        cv2.putText(frame, f"Frame Counter: {frame_counter}/{FRAME_THRESHOLD}", (30, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Tampilkan frame
        cv2.imshow("DEBUG Drowsiness Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Program selesai.")

if __name__ == "__main__":
    main()