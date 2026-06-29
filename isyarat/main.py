import cv2
import mediapipe as mp
import numpy as np
import threading
import queue
import os
import uuid
import sys
import traceback
from gtts import gTTS
import pygame
from collections import deque
from statistics import mode, StatisticsError

# ==========================
# FUNGSI UTAMA (DIBUNGKUS TRY-EXCEPT)
# ==========================
def main():
    print(" [1/5] Memulai inisialisasi Pygame Audio...")
    try:
        pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
    except Exception as e:
        print(f"❌ Gagal init Pygame: {e}")
        print("💡 Coba cabut/headset atau restart audio driver Windows.")
        return

    print("🚀 [2/5] Memulai Antrian Suara (Queue)...")
    speech_queue = queue.Queue()

    def tts_worker():
        print(" [OK] Worker Suara Google Siap!")
        while True:
            text = speech_queue.get()
            if text is None:
                break
            
            temp_file = f"temp_{uuid.uuid4().hex}.mp3"
            try:
                tts = gTTS(text=text, lang='id', slow=False) 
                tts.save(temp_file)
                
                sound = pygame.mixer.Sound(temp_file)
                sound.play()
                
                while pygame.mixer.get_busy():
                    pygame.time.wait(100)
            except Exception as e:
                print(f"❌ Error suara: {e}")
            finally:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            speech_queue.task_done()

    threading.Thread(target=tts_worker, daemon=True).start()

    print("🚀 [3/5] Memulai MediaPipe Hands...")
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

    print("🚀 [4/5] Mencoba membuka Kamera...")
    cap = cv2.VideoCapture(0)
    
    # Cek apakah kamera benar-benar terbuka
    if not cap.isOpened():
        print("\n❌❌ ERROR FATAL: Kamera tidak bisa dibuka! ❌❌❌")
        print("Penyebab umum:")
        print("1. Kamera sedang dipakai aplikasi lain (Zoom, Discord, Teams).")
        print("2. Driver kamera bermasalah.")
        print("3. Index kamera bukan 0 (coba colok ulang webcam).")
        print("\nTekan Enter untuk keluar...")
        input()
        return

    print("🚀 [5/5] Kamera Berhasil! Memulai Loop Deteksi...")
    print("="*50)

    # ==========================
    # FUNGSI DETEKSI GESTURE
    # ==========================
    def deteksi_gesture_khusus(landmarks):
        jari_naik = []
        if landmarks[8].y < landmarks[6].y - 0.02: jari_naik.append(1)
        else: jari_naik.append(0)
        if landmarks[12].y < landmarks[10].y - 0.02: jari_naik.append(1)
        else: jari_naik.append(0)
        if landmarks[16].y < landmarks[14].y - 0.02: jari_naik.append(1)
        else: jari_naik.append(0)
        if landmarks[20].y < landmarks[18].y - 0.02: jari_naik.append(1)
        else: jari_naik.append(0)
        
        total_jari_naik = sum(jari_naik)
        
        if total_jari_naik == 1 and jari_naik[0] == 1:
            return "NADJIB", "Nadjib", total_jari_naik 
        elif total_jari_naik == 0:
            return "MY NAME IS", "Nama saya", total_jari_naik
        elif total_jari_naik == 4:
            return "HALO", "Halo", total_jari_naik
        
        return None, None, total_jari_naik 

    # ==========================
    # LOOP UTAMA
    # ==========================
    prediction_buffer = deque(maxlen=10) 
    current_prediction = "-"
    current_speech_text = ""
    last_spoken_text = "" 
    current_finger_count = 0

    while True:
        success, frame = cap.read()
        if not success:
            print("️ Gagal membaca frame kamera. Keluar...")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        detected_gesture = None
        speech_text = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                detected_gesture, speech_text, current_finger_count = deteksi_gesture_khusus(hand_landmarks.landmark)
                if detected_gesture:
                    prediction_buffer.append((detected_gesture, speech_text))

            if len(prediction_buffer) > 0:
                try:
                    gestures_only = [item[0] for item in prediction_buffer]
                    most_common = mode(gestures_only)
                    for item in prediction_buffer:
                        if item[0] == most_common:
                            current_prediction = item[0]
                            current_speech_text = item[1]
                            break
                except StatisticsError:
                    current_prediction = prediction_buffer[-1][0]
                    current_speech_text = prediction_buffer[-1][1]
            else:
                current_prediction = "-"
                current_speech_text = ""
        else:
            prediction_buffer.clear()
            current_prediction = "-"
            current_speech_text = ""
            current_finger_count = 0

        # Logika Suara
        if current_prediction != "-" and current_prediction != last_spoken_text and current_speech_text:
            last_spoken_text = current_prediction
            speech_queue.put(current_speech_text)
            print(f"✅ Masuk antrian: {current_speech_text}")
        elif current_prediction == "-":
            last_spoken_text = ""

        # Tampilkan Hasil
        if current_prediction == "HALO": color = (0, 255, 0) 
        elif current_prediction == "MY NAME IS": color = (255, 0, 0) 
        elif current_prediction == "NADJIB": color = (0, 165, 255) 
        else: color = (255, 255, 255) 

        cv2.putText(frame, f"{current_prediction}", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 3, color, 5)
        cv2.putText(frame, f"Jari: {current_finger_count}/4", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, "ESC: Exit", (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Gesture Voice Recognition", frame)

        key = cv2.waitKey(1)
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.quit()
    print("👋 Aplikasi ditutup dengan rapi.")

# ==========================
# GLOBAL ERROR HANDLER
# ==========================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n" + "="*50)
        print("💥 TERJADI ERROR TAK TERDUGA!")
        print("="*50)
        traceback.print_exc() # Ini akan menampilkan detail error yang sebenarnya
        print("\nTekan Enter untuk keluar...")
        input()