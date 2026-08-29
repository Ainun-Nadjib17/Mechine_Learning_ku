import cv2
import mediapipe as mp
import time
import threading
import os
import pygame
import webbrowser
from gtts import gTTS
from collections import deque
import ai_assistant

# --- Inisialisasi Pygame Mixer untuk Audio ---
pygame.mixer.init()

# --- Konfigurasi ---
AUDIO_FOLDER = "audio_cache"
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

GITHUB_URL = "https://ainun-nadjib17.github.io/AinunNadjib.github.io/"

AI_SCRIPT = """
This is the portfolio of Mokhamad Ainun Nadjib. 
He is an enthusiastic Junior Web Developer building websites using Python, Laravel, and Flutter.
Besides coding, he has unique interests as a Sambo Champion in East Java, 
and also a National Best Writer. 
His expertise includes Cyber Security, Machine Learning, and mobile app development.
"""

messages = [
    "AI Mode Active",  
    "Let me introduce myself, my name is Agil Hajrin Nugroho, you can call me Agil",
    "I am from East Java, Malang city",
    "From Arsitecture Engineering study program",
    "Faculty of Science and Technology",
    "Garda Zeno Of citium"
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
ok_gesture_triggered = False

audio_lock = threading.Lock()

finger_buffer = deque([0], maxlen=5)
ok_gesture_buffer = deque([False], maxlen=5)

def speak_and_browser_sequence():
    """Fungsi Khusus Jari Ke-6 (Kepalan/0) - Versi EN"""
    global is_speaking, ai_sequence_active, last_spoken_count
    
    if ai_sequence_active:
        return
        
    ai_sequence_active = True
    is_speaking = True
    
    try:
        intro_text = "Let my AI continue"
        intro_file = os.path.join(AUDIO_FOLDER, "ai_intro_en.mp3")
        if not os.path.exists(intro_file):
            tts = gTTS(text=intro_text, lang='en')
            tts.save(intro_file)
        
        with audio_lock:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(intro_file)
            time.sleep(0.1)
            pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        print("Opening Browser to GitHub...")
        webbrowser.open(GITHUB_URL)
        time.sleep(3) 
        
        ai_file = os.path.join(AUDIO_FOLDER, "ai_profile_en.mp3")
        if not os.path.exists(ai_file):
            tts = gTTS(text=AI_SCRIPT, lang='en')
            tts.save(ai_file)
            
        with audio_lock:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(ai_file)
            time.sleep(0.1)
            pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Error AI Sequence: {e}")
    finally:
        is_speaking = False
        ai_sequence_active = False
        last_spoken_count = -1 

def speak_google_normal(text, filename):
    """Fungsi suara biasa untuk jari 1-5 - RESPONSIVE VERSION"""
    global is_speaking
    
    is_speaking = True
    base_name = os.path.splitext(filename)[0]
    filepath = os.path.join(AUDIO_FOLDER, f"{base_name}_en.mp3")
    
    try:
        if not os.path.exists(filepath):
            print(f"🎤 Generating: {text[:30]}...")
            tts = gTTS(text=text, lang='en')
            tts.save(filepath)
        
        # [FIX] STOP audio lama dan LANGSUNG putar audio baru
        with audio_lock:
            pygame.mixer.music.stop()  # Stop audio yang sedang jalan
            pygame.mixer.music.load(filepath)
            time.sleep(0.1)
            pygame.mixer.music.play()
            print(f"🔊 Playing: {text[:30]}...")
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        is_speaking = False

def get_stable_finger_count(raw_count):
    finger_buffer.append(raw_count)
    if len(finger_buffer) == 5:
        counts = list(finger_buffer)
        for i in range(5):
            if counts.count(counts[i]) >= 3:
                return counts[i]
        return last_spoken_count
    return raw_count

def is_ok_gesture(hand_landmarks):
    lm = hand_landmarks.landmark
    thumb_tip = lm[4]
    index_tip = lm[8]
    distance = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
    touching = distance < 0.05 
    
    middle_open = lm[12].y < lm[10].y
    ring_open = lm[16].y < lm[14].y
    pinky_open = lm[20].y < lm[18].y
    
    return touching and middle_open and ring_open and pinky_open

def get_stable_ok_gesture(raw_ok):
    ok_gesture_buffer.append(raw_ok)
    if len(ok_gesture_buffer) == 5:
        trues = sum(ok_gesture_buffer)
        return trues >= 3
    return False

def count_fingers_logic(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    pips = [2, 6, 10, 14, 18]
    count = 0
    landmarks = hand_landmarks.landmark
    
    if landmarks[tips[0]].x < landmarks[pips[0]].x:
        count += 1
    for i in range(1, 5):
        if landmarks[tips[i]].y < landmarks[pips[i]].y:
            count += 1
    return count

# --- Main Loop ---
cap = cv2.VideoCapture(0)
print("Starting Stable Mode + AI Features (Fist/OK Gesture) - English Version [RESPONSIVE]...")

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    image = cv2.flip(image, 1)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)
    
    raw_finger_count = 0
    stable_finger_count = 0
    text_to_display = "Detecting Hand..."
    raw_ok = False
    stable_ok = False
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            raw_ok = is_ok_gesture(hand_landmarks)
            stable_ok = get_stable_ok_gesture(raw_ok)
            
            raw_finger_count = count_fingers_logic(hand_landmarks)
            stable_finger_count = get_stable_finger_count(raw_finger_count)
            
            if stable_ok:
                text_to_display = "👌🏻 AI Assistant (OK Gesture)"
                current_time = time.time()
                
                if not ok_gesture_triggered and (current_time - last_speak_time > 2.0):
                    ok_gesture_triggered = True
                    last_speak_time = current_time
                    
                    thread = threading.Thread(target=ai_assistant.run_ai_sequence)
                    thread.daemon = True
                    thread.start()
                    
            elif 0 <= stable_finger_count < len(messages):
                text_to_display = messages[stable_finger_count]
                
                current_time = time.time()
                if stable_finger_count != last_spoken_count and (current_time - last_speak_time > 2.0):
                    ok_gesture_triggered = False
                    
                    if stable_finger_count == 0:
                        print(f"👊 Fist detected - Starting AI sequence")
                        thread = threading.Thread(target=speak_and_browser_sequence)
                        thread.start()
                    else:
                        audio_file = f"pesan_{stable_finger_count}.mp3"
                        print(f"✌️ Finger {stable_finger_count} detected")
                        thread = threading.Thread(target=speak_google_normal, args=(messages[stable_finger_count], audio_file))
                        thread.start()
                    
                    last_spoken_count = stable_finger_count
                    last_speak_time = current_time
            else:
                ok_gesture_triggered = False

    cv2.putText(image, text_to_display, (30, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
    
    if stable_ok:
        mode_text = "MODE: 👌🏻 OK GESTURE"
    elif stable_finger_count == 0:
        mode_text = "MODE AI (FIST)"
    else:
        mode_text = f"FINGERS: {stable_finger_count}"
        
    cv2.putText(image, mode_text, (30, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow('Stable Gesture + AI - Nadjib (EN)', image)
    
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()