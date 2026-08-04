import cv2
import mediapipe as mp
import time
import threading
import os
import pygame
import subprocess # Untuk memanggil file ai_assistant.py
import sys
from gtts import gTTS
from collections import deque
import math # Untuk menghitung jarak deteksi kepalan

# --- Inisialisasi Pygame Mixer untuk Audio ---
pygame.mixer.init()

# --- Konfigurasi ---
AUDIO_FOLDER = "audio_cache"
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

# Data Teks Utama (Index 1-5)
messages = [
    "Mode AI Aktif",  # Index 0 (Trigger untuk Jari Ke-6 / Kepalan)
    "Perkenalkan nama saya Mokhamad Ainun Nadjib, bisa dipanggil Nadjib", # Index 1
    "Asal saya dari Jawa Timur, kota Pasuruan", # Index 2
    "Dari prodi Teknik Informatika", # Index 3
    "Fakultas Sains dan Teknologi", # Index 4
    "Garda Paulo Freire 51" # Index 5
]

# --- Setup MediaPipe ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# --- Variabel Stabilisasi ---
last_spoken_count = -1
last_speak_time = 0
is_speaking = False
ai_process_running = False # Flag untuk mencegah multiple execution file AI

# Buffer untuk smoothing deteksi jari
finger_buffer = deque([0], maxlen=5)

def calculate_distance(p1, p2):
    """Hitung jarak antara dua titik landmark"""
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def trigger_ai_script():
    """Fungsi untuk menjalankan file ai_assistant.py secara terpisah"""
    global ai_process_running
    
    if ai_process_running:
        return
        
    ai_process_running = True
    print("🚀 Menjalankan ai_assistant.py...")
    
    try:
        # Menjalankan script python lain menggunakan subprocess
        # [sys.executable] memastikan menggunakan interpreter python yang sama
        subprocess.run([sys.executable, "ai_assistant.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error menjalankan AI script: {e}")
    except FileNotFoundError:
        print("❌ File 'ai_assistant.py' tidak ditemukan! Pastikan ada di folder yang sama.")
    finally:
        ai_process_running = False
        print("✅ AI script selesai.")
        # Reset last_spoken_count agar bisa dipicu lagi kalau tangan diturunkan lalu dikepal lagi
        global last_spoken_count
        last_spoken_count = -1

def speak_google_normal(text, filename):
    """Fungsi suara biasa untuk jari 1-5"""
    global is_speaking
    if is_speaking:
        return
    
    is_speaking = True
    filepath = os.path.join(AUDIO_FOLDER, filename)
    
    try:
        if not os.path.exists(filepath):
            tts = gTTS(text=text, lang='id')
            tts.save(filepath)
        
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        is_speaking = False

def get_stable_finger_count(raw_count):
    """Logika Smoothing"""
    finger_buffer.append(raw_count)
    if len(finger_buffer) == 5:
        counts = list(finger_buffer)
        for i in range(5):
            if counts.count(counts[i]) >= 3:
                return counts[i]
        return last_spoken_count
    return raw_count

def count_fingers_logic(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    pips = [2, 6, 10, 14, 18]
    count = 0
    landmarks = hand_landmarks.landmark
    
    # --- LOGIKA KEPALAN (JARI KE-6 / RETURN 0) YANG DIPERBAIKI ---
    # Mengecek apakah semua ujung jari berada DI BAWAH sendi PIP-nya
    # Ini jauh lebih stabil daripada mengukur jarak ke wrist
    fingers_closed = 0
    for i in range(1, 5):  # Cek 4 jari selain jempol
        if landmarks[tips[i]].y > landmarks[pips[i]].y:
            fingers_closed += 1
            
    # Jempol juga harus tertutup untuk dianggap kepalan sempurna
    # Membandingkan tip jempol dengan IP joint (index 3)
    if landmarks[tips[0]].y > landmarks[3].y: 
        fingers_closed += 1

    # Jika 4 atau 5 jari benar-benar tertekuk ke bawah, baru return 0 (AI Trigger)
    if fingers_closed >= 4:
        return 0

    # --- LOGIKA HITUNG JARI BIASA (1-5) YANG DIPERBAIKI ---
    # Jempol: Gunakan perbandingan Y terhadap IP joint (index 3) 
    # Lebih stabil terhadap rotasi tangan dibanding sumbu X
    if landmarks[tips[0]].y < landmarks[3].y:
        count += 1
        
    # 4 Jari lainnya (Telunjuk, Tengah, Manis, Kelingking)
    for i in range(1, 5):
        if landmarks[tips[i]].y < landmarks[pips[i]].y:
            count += 1
            
    return count

# --- Main Loop ---
cap = cv2.VideoCapture(0)
print("Memulai Mode Stabil + Fitur AI (Panggil File Terpisah)...")
print("Pastikan file 'ai_assistant.py' ada di folder yang sama!")

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    image = cv2.flip(image, 1)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)
    
    raw_finger_count = 0
    stable_finger_count = 0
    text_to_display = "Deteksi Tangan..."
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            raw_finger_count = count_fingers_logic(hand_landmarks)
            stable_finger_count = get_stable_finger_count(raw_finger_count)
            
            if 0 <= stable_finger_count < len(messages):
                text_to_display = messages[stable_finger_count]
                
                current_time = time.time()
                # Delay 2 detik
                if stable_finger_count != last_spoken_count and (current_time - last_speak_time > 2.0):
                    
                    if stable_finger_count == 0:
                        # --- FITUR JARI KE-6 (KEPALAN TANGAN) ---
                        # Panggil fungsi trigger file terpisah
                        thread = threading.Thread(target=trigger_ai_script)
                        thread.start()
                    else:
                        # --- SUARA BIASA (JARI 1-5) ---
                        audio_file = f"pesan_{stable_finger_count}.mp3"
                        thread = threading.Thread(target=speak_google_normal, args=(messages[stable_finger_count], audio_file))
                        thread.start()
                    
                    last_spoken_count = stable_finger_count
                    last_speak_time = current_time

    # Tampilan UI
    cv2.putText(image, text_to_display, (30, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
    
    # Debug info
    mode_text = "MODE AI (KEPAL)" if stable_finger_count == 0 else f"JARI: {stable_finger_count}"
    cv2.putText(image, mode_text, (30, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow('Gesture Stabil + AI - Nadjib', image)
    
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()