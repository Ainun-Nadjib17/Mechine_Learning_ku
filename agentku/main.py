import speech_recognition as sr
import pyttsx3
import webbrowser
import subprocess
import time
import os

class AsistenAI:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Initialize text-to-speech
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)

        # Status
        self.is_running = True

        # Edge path (default Windows)
        kandidat = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        ]
        self.edge_path = next((p for p in kandidat if os.path.exists(p)), None)

    def bicara(self, teks):
        print(f"[AI] {teks}")
        self.engine.say(teks)
        self.engine.runAndWait()

    def buka_edge(self, url=None):
        if self.edge_path:
            cmd = [self.edge_path]
            if url:
                cmd.append(url)
            subprocess.Popen(cmd)
        else:
            webbrowser.open(url or "https://www.google.com")
        time.sleep(2)

    def dengarkan(self):
        print("[*] Mendengarkan...")
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            print("[!] Tidak ada suara terdeteksi.")
            return None
        try:
            perintah = self.recognizer.recognize_google(audio, language="id-ID")
            print(f"[Anda] {perintah}")
            return perintah.lower()
        except sr.UnknownValueError:
            print("[!] Maaf, suara tidak jelas.")
            return None
        except sr.RequestError as e:
            print(f"[!] Layanan suara error: {e}")
            return None

    def proses(self, perintah):
        if any(k in perintah for k in ["open edge", "buka edge", "open browser", "buka browser"]):
            self.bicara("Membuka Edge...")
            self.buka_edge()
        elif "youtube" in perintah:
            self.bicara("Membuka YouTube...")
            self.buka_edge("https://www.youtube.com")
        elif "facebook" in perintah:
            self.bicara("Membuka Facebook...")
            self.buka_edge("https://www.facebook.com")
        elif perintah.startswith("search") or perintah.startswith("cari"):
            query = perintah.replace("search", "").replace("cari", "").strip()
            if query:
                self.bicara(f"Mencari {query} di Google...")
                self.buka_edge("https://www.google.com/search?q=" + query.replace(" ", "+"))
            else:
                self.bicara("Mau cari apa? Contoh: cari lagu jazz")
        elif "keluar" in perintah or "exit" in perintah:
            self.bicara("Baik, sampai jumpa!")
            self.is_running = False
        else:
            self.bicara("Maaf, perintah tidak dikenali.")

    def run(self):
        print("=" * 50)
        print("ASISTEN AI - Voice Edge Controller")
        print("=" * 50)
        self.bicara("Halo! Saya asisten AI Anda.")
        self.bicara("Silakan beri perintah, contoh: open edge, atau search youtube")

        print("\n[*] Kalibrasi microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("[OK] Microphone siap!\n")

        print("Perintah suara yang tersedia:")
        print("- 'open edge'       -> Buka Edge")
        print("- 'search youtube'  -> Langsung ke YouTube")
        print("- 'search facebook' -> Langsung ke Facebook")
        print("- 'search [query]'  -> Cari di Google")
        print("- 'cari [query]'    -> Cari di Google")
        print("- 'keluar' / 'exit' -> Keluar program\n")

        while self.is_running:
            perintah = self.dengarkan()
            if perintah:
                self.proses(perintah)
            time.sleep(0.3)

if __name__ == "__main__":
    try:
        AsistenAI().run()
    except KeyboardInterrupt:
        print("\n[*] Program dihentikan manual.")