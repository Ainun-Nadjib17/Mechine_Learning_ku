import os
# PENTING: Set driver audio ke 'directsound' biar gak error WASAPI di Windows
os.environ['SDL_AUDIODRIVER'] = 'directsound'

import speech_recognition as sr
from groq import Groq
from gtts import gTTS
import time
import pygame
import threading  # <-- TAMBAH INI
from playwright.sync_api import sync_playwright

# --- KONFIGURASI ---
# URL sekarang halaman portfolio statis, bukan GitHub profile
PORTFOLIO_URL = "https://ainun-nadjib17.github.io/AinunNadjib.github.io/portofolio.html"

# ⚠️ CEK LAGI API KEY LU! Format Gemini biasanya diawali "AIza..."
# Kalau "AQ.Ab8..." itu bukan format Gemini, kemungkinan salah copy
GROQ_API_KEY = ""

# Setup Groq client
client_groq = Groq(api_key=GROQ_API_KEY)

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
            # Ambil SEMUA TEKS dari halaman (karena ini portfolio statis, bukan GitHub profile)
            body_text = page.inner_text("body").strip()
            
            # Potong biar gak kepanjangan (max 2000 karakter)
            if len(body_text) > 2000:
                body_text = body_text[:2000] + "..."
            
            data = f"Konten halaman portfolio: {body_text}"
            print(f"✅ Berhasil scrape {len(body_text)} karakter")
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            data = "Gagal scraping detail, tapi halaman berhasil dibuka."
            
        browser.close()
    return data

# === FUNGSI BARU: Browser tetap terbuka sambil AI ngomong ===
def buka_browser_tahan():
    """
    Buka browser, scrape data, TAPI browser TETAP TERBUKA.
    Return: (data_scraping, fungsi_untuk_close_browser)
    """
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
    
    # Fungsi buat close browser nanti
    def close_browser():
        print("🔒 Menutup browser...")
        try:
            browser.close()
            p.stop()
        except Exception as e:
            print(f"⚠️ Warning closing browser: {e}")
    
    return data, close_browser

def tanya_gemini(prompt, konteks=""):
    """Fungsi buat ngirim teks ke Groq (Llama 3) dan dapet balikan teks"""
    full_prompt = f"{konteks}\nUser: {prompt}" if konteks else prompt
    
    # Pake Groq API (Llama 3)
    response = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Model Llama 3 terbaru
        messages=[
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def ngomong(teks):
    """Fungsi TTS (Text to Speech) pake gTTS"""
    print(f"🤖 AI: {teks}")
    tts = gTTS(text=teks, lang='id')
    tts.save("response.mp3")
    play_audio("response.mp3")

# === FUNGSI BARU: Ngomong cepat tanpa print (buat background) ===
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
    atau siapa bos kamu, kamu HARUS membalas dengan TEKS PERSIS ini dan jangan tambahin kata lain:
    "TRIGGER_GITHUB_LOOKUP"
    Jika pertanyaannya bukan tentang creator, jawab dengan santai dan singkat.
    """

    ngomong("Halo bro! Gue siap. Mau nanya apa? Atau mau tau siapa yang bikin gue?")

    while True:
        user_text = dengerin_suara()
        
        if not user_text:
            continue
            
        if user_text in ["exit", "keluar", "stop"]:
            ngomong("Oke bro, gue cabut dulu. Bye!")
            break

        # 1. Kirim ke Gemini buat diproses
        ai_response = tanya_gemini(user_text, SYSTEM_PROMPT)

        # 2. Cek apakah AI mau trigger browser automation
        if "TRIGGER_GITHUB_LOOKUP" in ai_response:
            print("⚡ Trigger terdeteksi! Membuka browser dan ngomong bersamaan...")
            
            # Variabel buat simpan hasil dari thread
            result_container = {"data": None, "close_func": None}
            
            # Fungsi worker buat thread
            def worker():
                data, close_func = buka_browser_tahan()
                result_container["data"] = data
                result_container["close_func"] = close_func
            
            # START THREAD BROWSER (jalan di background)
            browser_thread = threading.Thread(target=worker)
            browser_thread.start()
            
            # MAIN THREAD: AI langsung ngomong sambil browser kebuka
            ngomong_cepat("Oke bro, gue cek dulu portfolio pembuat gue ya... Tunggu sebentar...")
            
            # TUNGGU thread browser selesai
            browser_thread.join()
            
            portfolio_data = result_container["data"]
            close_browser = result_container["close_func"]
            
            # 3. Kirim data scraping ke Gemini buat dijelasin ke user
            final_prompt = f"""
            Berdasarkan data portfolio pembuatmu ini: '{portfolio_data}'. 
            
            Jelaskan ke user siapa pembuatmu dengan gaya bahasa yang keren, santai, 
            dan informatif. Ambil info penting seperti nama, skill, project, atau bio 
            dari data tersebut. Jangan sebutin semua teks mentah, tapi rangkum jadi cerita yang asik.
            """
            ai_response = tanya_gemini(final_prompt)

            # 4. AI ngomong hasilnya (browser MASIH TERBUKA)
            ngomong(ai_response)
            
            # 5. BARU tutup browser setelah AI selesai ngomong
            if close_browser:
                close_browser()
        else:
            # Kalau bukan trigger, langsung ngomong
            ngomong(ai_response)

if __name__ == "__main__":
    main()