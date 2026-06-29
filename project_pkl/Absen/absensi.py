import cv2
import os
import json
import numpy as np
from datetime import datetime

FACES_DIR = "faces"
ABSEN_FILE = "absensi.json"
os.makedirs(FACES_DIR, exist_ok=True)

# -----------------------------
# Fungsi bantu absensi
# -----------------------------
def load_absensi():
    if not os.path.exists(ABSEN_FILE):
        return {}
    with open(ABSEN_FILE, "r") as f:
        return json.load(f)

def save_absensi(data):
    with open(ABSEN_FILE, "w") as f:
        json.dump(data, f, indent=4)

def sudah_absen_hari_ini(nama, data_absensi):
    today = datetime.now().strftime("%Y-%m-%d")
    return nama in data_absensi and data_absensi[nama]["tanggal"] == today

# -----------------------------
# Fungsi bantu wajah
# -----------------------------
def ambil_gambar(judul_window="Kamera", simpan_path=None):
    cam = cv2.VideoCapture(0)
    print("📸 Tekan 's' untuk menyimpan gambar, 'q' untuk batal")

    captured = None
    while True:
        ret, frame = cam.read()
        if not ret:
            print("[❌] Kamera tidak terdeteksi!")
            break

        cv2.imshow(judul_window, frame)
        key = cv2.waitKey(1)

        if key == ord('s'):
            captured = frame
            if simpan_path:
                cv2.imwrite(simpan_path, frame)
                print(f"[✅] Gambar disimpan di {simpan_path}")
            break
        elif key == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    return captured

# -----------------------------
# Fungsi membandingkan wajah
# -----------------------------
def cek_kemiripan(img1, img2):
    # Ubah ke grayscale biar perbandingan adil
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Ubah ukuran agar sama
    img2_gray = cv2.resize(img2_gray, (img1_gray.shape[1], img1_gray.shape[0]))

    # Hitung histogram
    hist1 = cv2.calcHist([img1_gray], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([img2_gray], [0], None, [256], [0, 256])

    # Normalisasi
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)

    # Bandingkan (correlation)
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return similarity

# -----------------------------
# Registrasi wajah
# -----------------------------
def registrasi_wajah():
    nama = input("Masukkan nama untuk registrasi: ").strip()
    path = os.path.join(FACES_DIR, f"{nama}.jpg")

    if os.path.exists(path):
        print("[⚠️] Nama ini sudah terdaftar. File akan ditimpa.")

    ambil_gambar("Registrasi Wajah", simpan_path=path)

# -----------------------------
# Absensi wajah
# -----------------------------
def absen_wajah():
    nama = input("Masukkan nama untuk absen: ").strip()
    path = os.path.join(FACES_DIR, f"{nama}.jpg")

    if not os.path.exists(path):
        print("[❌] Nama tidak terdaftar!")
        return

    # Ambil foto baru
    gambar_baru = ambil_gambar("Absensi - Arahkan wajah ke kamera")

    if gambar_baru is None:
        print("[❌] Gagal mengambil gambar.")
        return

    # Baca foto terdaftar
    gambar_terdaftar = cv2.imread(path)

    # Cek kemiripan
    similarity = cek_kemiripan(gambar_terdaftar, gambar_baru)
    print(f"🔍 Nilai kemiripan: {similarity:.2f}")

    if similarity < 0.8:  # ambang batas bisa kamu sesuaikan
        print("[❌] Wajah tidak cocok! Absen ditolak.")
        return

    # Proses absensi
    absensi = load_absensi()
    if sudah_absen_hari_ini(nama, absensi):
        print("[⚠️] Kamu sudah absen hari ini!")
    else:
        now = datetime.now()
        absensi[nama] = {
            "tanggal": now.strftime("%Y-%m-%d"),
            "jam": now.strftime("%H:%M:%S")
        }
        save_absensi(absensi)
        print(f"[✅] Absen berhasil! {nama} tercatat pada {absensi[nama]['tanggal']} {absensi[nama]['jam']}")

# -----------------------------
# Menu utama
# -----------------------------
def main():
    while True:
        print("\n=== 📚 Sistem Absensi Wajah (Tanpa face_recognition) ===")
        print("1. Registrasi Wajah")
        print("2. Absen Wajah")
        print("3. Keluar")

        pilihan = input("Pilih menu: ")

        if pilihan == "1":
            registrasi_wajah()
        elif pilihan == "2":
            absen_wajah()
        elif pilihan == "3":
            print("👋 Keluar...")
            break
        else:
            print("[⚠️] Pilihan tidak valid.")

if __name__ == "__main__":
    main()
