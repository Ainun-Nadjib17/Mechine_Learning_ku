import cv2
import pygame
from gtts import gTTS
import os
import time
from ultralytics import YOLO

# 1. Inisialisasi Audio Warning
def play_warning(text, filename="warning.mp3"):
    # Buat file audio dari teks jika belum ada
    if not os.path.exists(filename):
        tts = gTTS(text=text, lang='id')
        tts.save(filename)
    
    # Putar audio menggunakan pygame
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

# Buat audio peringatan awal
play_warning("Awas ada pencuri masuk", "masuk.mp3")
play_warning("Barang telah dicuri", "dicuri.mp3")

# 2. Load Model YOLOv8 (Model standar COCO yang bisa deteksi 'person', 'bottle', dll)
model = YOLO('yolov8n.pt')

# 3. Buka Webcam (0 untuk kamera bawaan laptop)
cap = cv2.VideoCapture(0)

# Status pelacakan
person_detected = False
bottle_detected = False
last_alarm_time = 0

print("Program Pendeteksi Sistem Keamanan Berjalan...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Jalankan Deteksi Objek YOLO
    results = model(frame, stream=True, verbose=False)

    current_person = False
    current_bottle = False

    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Ambil Class ID & Nama Objek
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]
            confidence = float(box.conf[0])

            # Ambil koordinat Bounding Box
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Deteksi Manusia (Person)
            if class_name == 'person' and confidence > 0.5:
                current_person = True
                # Gambar kotak hijau
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"PENCURI: {confidence:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Deteksi Objek Barang (misal: Botol/Bottle)
            if class_name == 'bottle' and confidence > 0.4:
                current_bottle = True
                # Gambar kotak biru
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, "BARANG (BOTOL)", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # Logika Notifikasi Suara (Cooldown 3 detik agar tidak spam)
    current_time = time.time()
    
    # 1. Jika Pencuri/Orang Baru Terdeteksi
    if current_person and not person_detected:
        if current_time - last_alarm_time > 3:
            print("--> AWAS ADA PENCURI MASUK!")
            pygame.mixer.music.load("masuk.mp3")
            pygame.mixer.music.play()
            last_alarm_time = current_time

    # 2. Jika Barang/Botol Hilang (Diambil)
    if bottle_detected and not current_bottle:
        if current_time - last_alarm_time > 3:
            print("--> BARANG TELAH DICURI!")
            pygame.mixer.music.load("dicuri.mp3")
            pygame.mixer.music.play()
            last_alarm_time = current_time

    person_detected = current_person
    bottle_detected = current_bottle

    # Tampilkan Video Feed
    cv2.imshow("Sistem Keamanan Deteksi Pencuri", frame)

    # Tekan 'q' untuk keluar
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()