import cv2
import mediapipe as mp
import time
import threading
import os
import pygame
import webbrowser
from gtts import gTTS
from collections import deque
import ai_assistant  # [BARU] Import modul eksternal sesuai request

# --- Inisialisasi Pygame Mixer untuk Audio ---
pygame.mixer.init()

# --- Konfigurasi ---
AUDIO_FOLDER = "audio_cache"
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

GITHUB_URL = "https://ainun-nadjib17.github.io/AinunNadjib.github.io/"

# Skrip AI untuk dibacakan (Berdasarkan isi GitHub kamu)
AI_SCRIPT = """
Ini adalah portofolio dari Mokhamad Ainun Nadjib. 
Dia adalah Junior Web Developer yang antusias membangun website menggunakan Python, Laravel, dan Flutter.
Selain coding, dia memiliki ketertarikan unik yaitu sebagai Juara Sambo tingkat Jawa Timur, 
dan juga seorang Penulis Terbaik Nasional. 
Keahliannya mencakup Cyber Security, Machine Learning, dan pengembangan aplikasi mobile.
"""

# Data Teks Utama (Index 1-5)
# Index 0 kita kosongkan atau isi placeholder, karena 0 akan jadi trigger AI
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
ai_sequence_active = False
ok_gesture_triggered = False  # [BARU] Flag khusus gestur OK

# Buffer untuk smoothing deteksi jari
finger_buffer = deque([0], maxlen=5)
# [BARU] Buffer khusus smoothing gestur OK agar tidak flicker
ok_gesture_buffer = deque([False], maxlen=5)

def speak_and_browser_sequence():
    """Fungsi Khusus Jari Ke-6 (Kepalan/0): Bicara -> Buka Browser -> Bicara AI"""
    global is_speaking, ai_sequence_active, last_spoken_count
    
    if is_speaking or ai_sequence_active:
        return
        
    ai_sequence_active = True
    is_speaking = True
    
    try:
        # 1. Suara Intro
        intro_text = "Biarkan AI saya yang melanjutkan"
        intro_file = os.path.join(AUDIO_FOLDER, "ai_intro.mp3")
        if not os.path.exists(intro_file):
            tts = gTTS(text=intro_text, lang='id')
            tts.save(intro_file)
        
        pygame.mixer.music.load(intro_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        # 2. Buka Browser
        print("Membuka Browser ke GitHub...")
        webbrowser.open(GITHUB_URL)
        
        # Jeda loading
        time.sleep(3) 
        
        # 3. Suara AI Menjelaskan Profil
        ai_file = os.path.join(AUDIO_FOLDER, "ai_profile.mp3")
        if not os.path.exists(ai_file):
            tts = gTTS(text=AI_SCRIPT, lang='id')
            tts.save(ai_file)
            
        pygame.mixer.music.load(ai_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Error AI Sequence: {e}")
    finally:
        is_speaking = False
        ai_sequence_active = False
        # Reset agar bisa dipicu lagi kalau tangan diturunkan lalu dikepal lagi
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

# [BARU] Fungsi Deteksi Gestur OK 👌🏻
def is_ok_gesture(hand_landmarks):
    """
    Mendeteksi gestur OK dengan membandingkan jarak ujung jempol & telunjuk
    terhadap jari-jari lain yang harus terbuka.
    """
    lm = hand_landmarks.landmark
    
    # Ujung Jempol (4) dan Telunjuk (8) harus berdekatan
    thumb_tip = lm[4]
    index_tip = lm[8]
    
    # Hitung jarak euclidean sederhana antara jempol dan telunjuk
    distance = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
    
    # Threshold kedekatan (sesuaikan jika perlu, 0.05 biasanya cukup untuk webcam)
    touching = distance < 0.05 
    
    # Pastikan jari Tengah(12), Manis(16), Kelingking(20) TEBUKA (y tip < y pip)
    middle_open = lm[12].y < lm[10].y
    ring_open = lm[16].y < lm[14].y
    pinky_open = lm[20].y < lm[18].y
    
    return touching and middle_open and ring_open and pinky_open

# [BARU] Smoothing khusus gestur OK
def get_stable_ok_gesture(raw_ok):
    ok_gesture_buffer.append(raw_ok)
    if len(ok_gesture_buffer) == 5:
        trues = sum(ok_gesture_buffer)
        return trues >= 3  # Stabil jika minimal 3 dari 5 frame terakhir True
    return False

def count_fingers_logic(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    pips = [2, 6, 10, 14, 18]
    count = 0
    landmarks = hand_landmarks.landmark
    
    # Jempol
    if landmarks[tips[0]].x < landmarks[pips[0]].x:
        count += 1
    # 4 Jari lain
    for i in range(1, 5):
        if landmarks[tips[i]].y < landmarks[pips[i]].y:
            count += 1
    return count

# --- Main Loop ---
cap = cv2.VideoCapture(0)
print("Memulai Mode Stabil + Fitur AI (Jari 6/Kepalan) + Gestur OK 👌🏻...")

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
    raw_ok = False
    stable_ok = False
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # [BARU] Cek gestur OK terlebih dahulu
            raw_ok = is_ok_gesture(hand_landmarks)
            stable_ok = get_stable_ok_gesture(raw_ok)
            
            # Logika jari tetap dijalankan untuk tampilan UI
            raw_finger_count = count_fingers_logic(hand_landmarks)
            stable_finger_count = get_stable_finger_count(raw_finger_count)
            
            # [BARU] PRIORITAS: Jika Gestur OK terdeteksi stabil
            if stable_ok:
                text_to_display = "👌🏻 AI Assistant (OK Gesture)"
                current_time = time.time()
                
                # Trigger hanya sekali per gestur, dengan cooldown 2 detik
                if not ok_gesture_triggered and (current_time - last_speak_time > 2.0):
                    ok_gesture_triggered = True
                    last_speak_time = current_time
                    
                    # Jalankan ai_assistant.py di thread terpisah agar kamera tidak freeze
                    thread = threading.Thread(target=ai_assistant.run_ai_sequence)
                    thread.daemon = True
                    thread.start()
                    
            elif 0 <= stable_finger_count < len(messages):
                text_to_display = messages[stable_finger_count]
                
                current_time = time.time()
                # Delay 2 detik
                if stable_finger_count != last_spoken_count and (current_time - last_speak_time > 2.0):
                    
                    # Reset flag OK gesture saat pindah ke mode jari biasa
                    ok_gesture_triggered = False
                    
                    if stable_finger_count == 0:
                        # --- FITUR JARI KE-6 (KEPALAN TANGAN) ---
                        thread = threading.Thread(target=speak_and_browser_sequence)
                        thread.start()
                    else:
                        # --- SUARA BIASA (JARI 1-5) ---
                        audio_file = f"pesan_{stable_finger_count}.mp3"
                        thread = threading.Thread(target=speak_google_normal, args=(messages[stable_finger_count], audio_file))
                        thread.start()
                    
                    last_spoken_count = stable_finger_count
                    last_speak_time = current_time
            else:
                # Tidak ada gestur valid, reset flag OK
                ok_gesture_triggered = False

    # Tampilan UI
    cv2.putText(image, text_to_display, (30, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
    
    # Debug info
    if stable_ok:
        mode_text = "MODE: 👌🏻 OK GESTURE"
    elif stable_finger_count == 0:
        mode_text = "MODE AI (KEPAL)"
    else:
        mode_text = f"JARI: {stable_finger_count}"
        
    cv2.putText(image, mode_text, (30, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow('Gesture Stabil + AI - Nadjib', image)
    
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()