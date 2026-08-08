import webbrowser
import time
import os
import pygame
from gtts import gTTS

# --- Configuration ---
AUDIO_FOLDER = "audio_cache"
GITHUB_URL = "https://ainun-nadjib17.github.io/AinunNadjib.github.io/"

# [EN] AI Script - FULL ENGLISH
AI_SCRIPT = """
This is the portfolio of Mokhamad Ainun Nadjib. 
He is an enthusiastic Junior Web Developer building websites using Python, Laravel, and Flutter.
Besides coding, he has unique interests as a Sambo Champion in East Java, 
and also a National Best Writer. 
His expertise includes Cyber Security, Machine Learning, and mobile app development.
"""

def run_ai_sequence():
    """Main function called from main.py - Fixed English Version"""
    print("🤖 AI Assistant: Starting English sequence...")
    
    if not os.path.exists(AUDIO_FOLDER):
        os.makedirs(AUDIO_FOLDER)

    # [FIX] Reset mixer untuk mencegah conflict audio lama
    try:
        pygame.mixer.quit()
        pygame.mixer.init()
    except Exception:
        pygame.mixer.init()

    try:
        # 1. Intro Voice
        intro_text = "Let my AI continue"
        intro_file = os.path.join(AUDIO_FOLDER, "ai_intro_en_v2.mp3")  # [FIX] Ganti nama versi
        
        # [FIX] Force regenerate jika file tidak ada ATAU ukurannya terlalu kecil (corrupt)
        if not os.path.exists(intro_file) or os.path.getsize(intro_file) < 1000:
            print("🤖 AI: Generating FRESH English intro voice...")
            tts = gTTS(text=intro_text, lang='en', slow=False)
            tts.save(intro_file)
        
        print(" AI: Speaking English intro...")
        pygame.mixer.music.load(intro_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        # 2. Open Browser
        print(f"AI: Opening {GITHUB_URL} ...")
        webbrowser.open(GITHUB_URL)
        time.sleep(3) 
        
        # 3. AI Profile Explanation
        ai_file = os.path.join(AUDIO_FOLDER, "ai_profile_en_v2.mp3")  # [FIX] Ganti nama versi
        
        if not os.path.exists(ai_file) or os.path.getsize(ai_file) < 1000:
            print(" AI: Generating FRESH English profile voice...")
            tts = gTTS(text=AI_SCRIPT, lang='en', slow=False)
            tts.save(ai_file)
            
        print("🤖 AI: Explaining profile in English...")
        pygame.mixer.music.load(ai_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        print("✅ English AI Sequence Completed.")

    except Exception as e:
        print(f"❌ Error in AI Assistant: {e}")


if __name__ == "__main__":
    run_ai_sequence()