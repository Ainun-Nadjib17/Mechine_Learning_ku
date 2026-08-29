import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from ultralytics import YOLO
from datetime import datetime
import os
import winsound
import threading
import time

# ==================================================
# CONFIG
# ==================================================

# Model dari: https://github.com/noorkhokhar99/Fire-Detection-using-YOLOv8
MODEL_PATH = "best.pt"

CONFIDENCE = 0.45
CAMERA_INDEX = 0
INFERENCE_SIZE = 320  # OPTIMASI: 320/416/640. Semakin kecil semakin cepat (sangat disarankan untuk CPU)

SAVE_DIR = "detections"
os.makedirs(SAVE_DIR, exist_ok=True)

# ==================================================
# LOAD MODEL
# ==================================================

try:
    # Biarkan device kosong untuk auto-detect (akan pakai GPU jika tersedia, jika tidak pakai CPU)
    model = YOLO(MODEL_PATH)
except Exception as e:
    model = None
    print("Model gagal dimuat:", e)

# ==================================================
# APP
# ==================================================

class FireDetectionApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Fire Detection System (Optimized)")
        self.root.geometry("1100x700")
        self.root.configure(bg="#202020")

        self.cap = None
        self.running = False

        self.last_alarm_time = 0
        self.alarm_cooldown = 2.0  # OPTIMASI: Jeda alarm 2 detik agar tidak spam
        self.alarm_active = False  # OPTIMASI: Flag untuk mencegah spam thread
        
        self.total_detection = 0

        self.create_ui()

    # ------------------------------------------------
    # UI
    # ------------------------------------------------

    def create_ui(self):
        header = tk.Frame(self.root, bg="#151515", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🔥 FIRE DETECTION SYSTEM", font=("Arial", 22, "bold"), fg="white", bg="#151515"
        ).pack(side="left", padx=20)

        self.online_label = tk.Label(
            header, text="● OFFLINE", font=("Arial", 14, "bold"), fg="#aaaaaa", bg="#151515"
        )
        self.online_label.pack(side="right", padx=20)

        main = tk.Frame(self.root, bg="#202020")
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # CAMERA
        camera_frame = tk.Frame(main, bg="black")
        camera_frame.pack(side="left", fill="both", expand=True)

        self.video_label = tk.Label(
            camera_frame, text="Kamera belum aktif", font=("Arial", 20), fg="white", bg="black"
        )
        self.video_label.pack(fill="both", expand=True)

        # SIDEBAR
        sidebar = tk.Frame(main, bg="#181818", width=280)
        sidebar.pack(side="right", fill="y", padx=(10, 0))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="STATUS", font=("Arial", 11, "bold"), fg="#aaaaaa", bg="#181818").pack(pady=(20, 5))

        self.status_label = tk.Label(
            sidebar, text="AMAN", font=("Arial", 27, "bold"), fg="#4CAF50", bg="#181818"
        )
        self.status_label.pack(pady=(0, 20))

        self.camera_stat = self.create_stat(sidebar, "Kamera", "OFF")
        self.fire_stat = self.create_stat(sidebar, "Api Terdeteksi", "0")
        self.conf_stat = self.create_stat(sidebar, "Confidence", "0%")

        # BUTTON
        tk.Button(
            sidebar, text="▶ MULAI KAMERA", command=self.start_camera, font=("Arial", 11, "bold"),
            bg="#2e7d32", fg="white", relief="flat"
        ).pack(fill="x", padx=20, pady=(30, 5), ipady=8)

        tk.Button(
            sidebar, text="■ STOP KAMERA", command=self.stop_camera, font=("Arial", 11, "bold"),
            bg="#b71c1c", fg="white", relief="flat"
        ).pack(fill="x", padx=20, pady=5, ipady=8)

        # LOG
        tk.Label(sidebar, text="LOG AKTIVITAS", font=("Arial", 11, "bold"), fg="#aaaaaa", bg="#181818").pack(pady=(25, 5))

        self.log = tk.Text(sidebar, bg="#0e0e0e", fg="white", font=("Consolas", 9), height=12)
        self.log.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    # ------------------------------------------------
    # STAT
    # ------------------------------------------------

    def create_stat(self, parent, name, value):
        frame = tk.Frame(parent, bg="#242424")
        frame.pack(fill="x", padx=15, pady=4)

        tk.Label(frame, text=name, fg="#aaaaaa", bg="#242424").pack(side="left", padx=10, pady=8)

        label = tk.Label(frame, text=value, fg="white", bg="#242424", font=("Arial", 10, "bold"))
        label.pack(side="right", padx=10)
        return label

    # ------------------------------------------------
    # LOG
    # ------------------------------------------------

    def add_log(self, text):
        now = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{now}] {text}\n")
        self.log.see("end")

    # ------------------------------------------------
    # START
    # ------------------------------------------------

    def start_camera(self):
        if model is None:
            messagebox.showerror("Model Error", f"Model fire belum tersedia.\n\nLetakkan file {MODEL_PATH} di folder yang sama.")
            return

        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Kamera tidak dapat dibuka.")
            return

        # OPTIMASI: Mengurangi latency antrian frame kamera
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.running = True
        self.online_label.config(text="● ONLINE", fg="#4CAF50")
        self.camera_stat.config(text="ON")
        self.add_log("Kamera dimulai.")
        self.update_frame()

    # ------------------------------------------------
    # STOP
    # ------------------------------------------------

    def stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

        self.online_label.config(text="● OFFLINE", fg="#aaaaaa")
        self.camera_stat.config(text="OFF")
        self.status_label.config(text="AMAN", fg="#4CAF50")
        self.video_label.config(image="", text="Kamera dihentikan")
        self.add_log("Kamera dihentikan.")
        self.alarm_active = False

    # ------------------------------------------------
    # DETECTION
    # ------------------------------------------------

    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.stop_camera()
            return

        frame = cv2.flip(frame, 1)

        fire_count = 0
        highest_conf = 0.0

        # OPTIMASI: Inference dengan imgsz yang lebih kecil untuk FPS lebih tinggi
        results = model.predict(
            frame,
            conf=CONFIDENCE,
            imgsz=INFERENCE_SIZE,
            verbose=False
        )

        result = results[0]

        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = model.names[cls].lower()

                # OPTIMASI: Model dari repo tersebut umumnya hanya punya 1 class: "fire"
                is_fire = (class_name == "fire" or len(model.names) == 1)

                if is_fire:
                    fire_count += 1
                    highest_conf = max(highest_conf, conf)

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(
                        frame, f"FIRE {conf*100:.1f}%", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                    )

        # ==============================
        # STATUS & LOGIC
        # ==============================
        if fire_count > 0:
            self.status_label.config(text="🔥 API TERDETEKSI", fg="#ff3333")
            self.fire_stat.config(text=str(fire_count))
            self.conf_stat.config(text=f"{highest_conf*100:.1f}%")

            cv2.rectangle(frame, (0, 0), (frame.shape[1], 55), (0, 0, 200), -1)
            cv2.putText(
                frame, "PERINGATAN: API TERDETEKSI!", (20, 37),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2
            )

            current_time = time.time()
            # OPTIMASI: Gunakan time delta untuk cooldown, jauh lebih stabil daripada .second
            if current_time - self.last_alarm_time >= self.alarm_cooldown:
                self.last_alarm_time = current_time
                self.total_detection += 1
                self.add_log(f"API TERDETEKSI - {highest_conf*100:.1f}%")
                
                # OPTIMASI: Mencegah spam thread alarm
                if not self.alarm_active:
                    self.alarm_active = True
                    threading.Thread(target=self.alarm, daemon=True).start()

        else:
            self.status_label.config(text="AMAN", fg="#4CAF50")
            self.fire_stat.config(text="0")
            self.conf_stat.config(text="0%")

        # ==============================
        # TIME & DISPLAY
        # ==============================
        cv2.putText(
            frame, datetime.now().strftime("%H:%M:%S"), (15, frame.shape[0] - 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

        # OPTIMASI: Resize frame untuk display agar lebih ringan daripada PIL thumbnail
        h, w = frame.shape[:2]
        max_h, max_w = 600, 780
        scale = min(max_w / w, max_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        display_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        display_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(display_frame)
        photo = ImageTk.PhotoImage(image)

        self.video_label.config(image=photo, text="")
        self.video_label.image = photo  # Keep reference agar tidak di-garbage collect

        self.root.after(20, self.update_frame)

    # ------------------------------------------------
    # ALARM
    # ------------------------------------------------

    def alarm(self):
        try:
            winsound.Beep(1200, 300)
            winsound.Beep(1500, 300)
        except Exception:
            # Fallback untuk non-Windows atau jika winsound gagal
            print("\a🔥 API TERDETEKSI!")
        finally:
            self.alarm_active = False

    # ------------------------------------------------
    # CLOSE
    # ------------------------------------------------

    def close(self):
        self.stop_camera()
        self.root.destroy()


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = FireDetectionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()