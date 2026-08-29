import os
# PENTING: Set driver audio ke 'directsound' biar gak error WASAPI di Windows
os.environ['SDL_AUDIODRIVER'] = 'directsound'

import speech_recognition as sr
from google import genai  # <-- MENGGUNAKAN PACKAGE BARU (RESMI DARI GOOGLE)
from gtts import gTTS
import time
import pygame
import threading
from playwright.sync_api import sync_playwright

# --- KONFIGURASI ---
PORTFOLIO_URL = "https://ainun-nadjib17.github.io/AinunNadjib.github.io/"

# ⚠️ MASUKKAN API KEY GEMINI DI SINI (Dimulai dengan "AIza...")
# Jika key lama masih error 404, BUAT KEY BARU di: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = ""

# Setup Google Gemini client (Package Baru)
client = genai.Client(api_key=GEMINI_API_KEY)

# Setup Pygame buat play audio
pygame.mixer.init()

def play_audio(file_path):
    """Fungsi buat play file MP3 dari gTTS"""
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.music.unload()

def dengerin_suara():
    """Fungsi buat input teks dari keyboard (sementara buat testing)"""
    try:
        text = input("🎙️  Ketik pertanyaan lu (atau 'exit' buat keluar): ")
        if text.strip():
            print(f"👤 Lu bilang: {text}")
        return text.lower()
    except Exception as e:
        print(f"❌ Error input: {e}")
        return ""

def buka_dan_scrape_portfolio():
    """Fungsi Playwright buat buka browser dan ambil teks portfolio"""
    print(f"🚀 Membuka browser ke {PORTFOLIO_URL}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(PORTFOLIO_URL)
        page.wait_for_timeout(3000)
        
        try:
            body_text = page.inner_text("body").strip()
            if len(body_text) > 2000:
                body_text = body_text[:2000] + "..."
            data = f"Konten halaman portfolio: {body_text}"
            print(f"✅ Berhasil scrape {len(body_text)} karakter")
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            data = "Gagal scraping detail, tapi halaman berhasil dibuka."
            
        browser.close()
    return data

def buka_browser_tahan():
    """Buka browser, scrape data, TAPI browser TETAP TERBUKA."""
    print(f"🚀 Membuka browser ke {PORTFOLIO_URL}...")
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(PORTFOLIO_URL)
    page.wait_for_timeout(3000)
    
    try:
        body_text = page.inner_text("body").strip()
        if len(body_text) > 2000:
            body_text = body_text[:2000] + "..."
        data = f"Konten halaman portfolio: {body_text}"
        print(f"✅ Berhasil scrape {len(body_text)} karakter")
        print("🌐 Browser TETAP TERBUKA sambil AI jelasin...")
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        data = "Gagal scraping detail, tapi halaman berhasil dibuka."
    
    def close_browser():
        print("🔒 Menutup browser...")
        try:
            browser.close()
            p.stop()
        except Exception as e:
            print(f"⚠️ Warning closing browser: {e}")
    
    return data, close_browser

def tanya_ai(prompt, konteks=""):
    """Fungsi buat ngirim teks ke Google Gemini dan dapet balikan teks"""
    full_prompt = f"{konteks}\nUser: {prompt}" if konteks else prompt
    
    try:
        # MENGGUNAKAN PACKAGE BARU: google.genai (Endpoint v1 yang stabil)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        print(f"❌ Error API Gemini: {e}")
        return "Maaf bro, lagi ada gangguan koneksi ke otak gue. Pastikan API Key lu bener, atau coba bikin API Key baru di Google AI Studio."

def ngomong(teks):
    """Fungsi TTS (Text to Speech) pake gTTS"""
    print(f"🤖 AI: {teks}")
    tts = gTTS(text=teks, lang='id')
    tts.save("response.mp3")
    play_audio("response.mp3")

def ngomong_cepat(teks):
    """Fungsi TTS tanpa print ke console"""
    tts = gTTS(text=teks, lang='id')
    tts.save("response_quick.mp3")
    play_audio("response_quick.mp3")

# --- LOGIC UTAMA ---
def main():
    SYSTEM_PROMPT = """
    Kamu adalah AI assistant yang santai dan cerdas. 
    ATURAN WAJIB: Jika user bertanya tentang siapa yang membuatmu, siapa creator kamu, 
    atau siapa bos kamu, kamu HARUS membalas dengan FUN FACT tentang pembuatmu. 
    Fun fact-nya: Namanya Mokhamad Ainun Nadjib (bisa dipanggil Nadjib). 
    Dia adalah National Best Writer, juara Sambo tingkat Jawa Timur, dan berasal dari Pasuruan, Jawa Timur. 
    Dia kuliah di Teknik Informatika, Fakultas Sains dan Teknologi. 
    Skill teknisnya mencakup Python, Laravel, Flutter, Cyber Security, Machine Learning, OpenCV, MediaPipe, dan gTTS. 
    Dia suka nambahin fitur keren seperti gesture tangan OK 👌🏻 di kodenya. 
    Sampaikan fun fact ini dengan gaya bahasa yang keren, santai, dan informatif.
    Jika pertanyaannya bukan tentang creator, jawab dengan santai dan singkat.
    """

    ngomong("Halo bro! Gue siap. Mau nanya apa? Atau mau tau fun fact tentang yang bikin gue?")

    while True:
        user_text = dengerin_suara()
        
        if not user_text:
            continue
            
        if user_text in ["exit", "keluar", "stop"]:
            ngomong("Oke bro, gue cabut dulu. Bye!")
            break

        # 1. Kirim ke Google Gemini buat diproses
        ai_response = tanya_ai(user_text, SYSTEM_PROMPT)

        # 2. Cek apakah AI mau trigger browser automation (jaga-jaga)
        if "TRIGGER_GITHUB_LOOKUP" in ai_response:
            print("⚡ Trigger terdeteksi! Membuka browser dan ngomong bersamaan...")
            
            result_container = {"data": None, "close_func": None}
            
            def worker():
                data, close_func = buka_browser_tahan()
                result_container["data"] = data
                result_container["close_func"] = close_func
            
            browser_thread = threading.Thread(target=worker)
            browser_thread.start()
            
            ngomong_cepat("Oke bro, gue cek dulu portfolio pembuat gue ya... Tunggu sebentar...")
            
            browser_thread.join()
            
            portfolio_data = result_container["data"]
            close_browser = result_container["close_func"]
            
            final_prompt = f"""
            Berdasarkan data portfolio pembuatmu ini: '{portfolio_data}'. 
            Jelaskan ke user siapa pembuatmu dengan gaya bahasa yang keren, santai, 
            dan informatif. Ambil info penting seperti nama, skill, project, atau bio 
            dari data tersebut. Jangan sebutin semua teks mentah, tapi rangkum jadi cerita yang asik.
            """
            ai_response = tanya_ai(final_prompt)

            ngomong(ai_response)
            
            if close_browser:
                close_browser()
        else:
            # Kalau bukan trigger, langsung ngomong
            ngomong(ai_response)

if __name__ == "__main__":
    main()