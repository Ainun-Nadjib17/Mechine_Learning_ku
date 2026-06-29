"""
security_realtime_no_screenshots.py

- Real-time monitoring tanpa menyimpan screenshot.
- Bunyi TTS langsung saat terdeteksi (pakai cache biar cepat).
- Log kejadian ditulis ke events/events.json (array entry).
- Tampilkan ROI + status di frame.

Kontrol:
 - 'r' lalu drag mouse = pilih ROI
 - 'c' = capture baseline (kondisi normal barang)
 - 'm' = on/off monitoring
 - 'q' = quit
"""

import cv2
import numpy as np
import os
import time
import threading
import json
from datetime import datetime
from gtts import gTTS
from playsound import playsound
from ultralytics import YOLO
import tempfile
import uuid

# ---------- Config ----------
ROI = None
SELECTING = False
ix = iy = -1

EVENTS_DIR = "events"
os.makedirs(EVENTS_DIR, exist_ok=True)
EVENTS_FILE = os.path.join(EVENTS_DIR, "events.json")

# load YOLO model
print("[INFO] Memuat model YOLO (yolov8n). Jika pertama kali, ini akan mendownload weights...")
model = YOLO("yolov8n.pt")

# Lock untuk penulisan log agar thread-safe
log_lock = threading.Lock()

# ---------- Mouse callback ----------
def on_mouse(event, x, y, flags, param):
    global ix, iy, ROI, SELECTING
    if event == cv2.EVENT_LBUTTONDOWN:
        SELECTING = True
        ix, iy = x, y
        ROI = None
    elif event == cv2.EVENT_MOUSEMOVE and SELECTING:
        frame = param['frame_copy']
        fcopy = frame.copy()
        cv2.rectangle(fcopy, (ix, iy), (x, y), (0,255,0), 2)
        cv2.imshow(param['win_name'], fcopy)
    elif event == cv2.EVENT_LBUTTONUP:
        SELECTING = False
        x0, y0 = min(ix, x), min(iy, y)
        x1, y1 = max(ix, x), max(iy, y)
        ROI = (x0, y0, x1, y1)
        print(f"[INFO] ROI dipilih: {ROI}")

# ---------- TTS play (lebih responsif dengan cache) ----------
ALARM_FILE = os.path.join(tempfile.gettempdir(), "alarm_cached.mp3")

# Pre-generate suara alarm saat pertama kali dijalankan
if not os.path.exists(ALARM_FILE):
    print("[INFO] Membuat file TTS alarm pertama kali...")
    try:
        tts = gTTS("Perhatian! Barang Anda sedang dicuri!", lang='id')
        tts.save(ALARM_FILE)
        print("[OK] File alarm berhasil dibuat dan disimpan ke cache.")
    except Exception as e:
        print("[ERR] Gagal membuat file TTS:", e)

def play_tts(text=None, lang='id'):
    """Mainkan suara alarm secara cepat (non-blocking) tanpa generate ulang."""
    def _play():
        try:
            playsound(ALARM_FILE)
        except Exception as e:
            print("[ERR] Gagal mainkan TTS:", e)
    thr = threading.Thread(target=_play, daemon=True)
    thr.start()

# ---------- Logging (no screenshots) ----------
def log_event(reason):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reason": reason
    }
    with log_lock:
        try:
            if os.path.exists(EVENTS_FILE):
                with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []
        except Exception:
            data = []

        data.append(entry)
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[LOG] {entry['timestamp']} - {reason}")

# ---------- Image helpers ----------
def prepare_gray(img, size=None):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if size is not None:
        g = cv2.resize(g, size)
    return g

def percent_diff(img1_gray, img2_gray, thresh=30):
    diff = cv2.absdiff(img1_gray, img2_gray)
    _, th = cv2.threshold(diff, thresh, 255, cv2.THRESH_BINARY)
    nz = np.count_nonzero(th)
    total = th.size
    return nz / total

def motion_score(prev_gray, cur_gray, thresh=25):
    diff = cv2.absdiff(prev_gray, cur_gray)
    _, th = cv2.threshold(diff, thresh, 255, cv2.THRESH_BINARY)
    return np.count_nonzero(th) / th.size

# ---------- Main ----------
def main():
    global ROI
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERR] Gagal membuka kamera.")
        return

    win_name = "Security Real-time Monitor"
    cv2.namedWindow(win_name)
    mouse_param = {'frame_copy': None, 'win_name': win_name}
    cv2.setMouseCallback(win_name, on_mouse, mouse_param)

    baseline_gray = None
    baseline_time = None
    prev_roi_gray = None
    monitoring = False
    last_alarm = 0
    alarm_cooldown = 6  # detik antar alarm

    print("Instruksi:")
    print(" - Tekan 'r' lalu drag untuk pilih ROI")
    print(" - Tekan 'c' untuk capture baseline (kondisi normal barang)")
    print(" - Tekan 'm' untuk mulai/stop monitoring")
    print(" - Tekan 'q' untuk keluar")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERR] Frame tidak tersedia.")
            break

        display = frame.copy()
        mouse_param['frame_copy'] = frame

        if ROI:
            x0, y0, x1, y1 = ROI
            cv2.rectangle(display, (x0, y0), (x1, y1), (0, 255, 0), 2)

        if baseline_gray is not None:
            cv2.putText(display, f"Baseline: {baseline_time}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 200), 2)

        status_text = "TIDAK DIAWASI"
        status_color = (0, 200, 0)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Keluar...")
            break
        elif key == ord('r'):
            print("Mulai pilih ROI: drag mouse lalu lepaskan.")
        elif key == ord('c'):
            if not ROI:
                print("[WARN] Pilih ROI dulu (r + drag).")
            else:
                x0, y0, x1, y1 = ROI
                roi_img = frame[y0:y1, x0:x1]
                if roi_img.size == 0:
                    print("[ERR] ROI kosong, ulangi.")
                else:
                    baseline_gray = prepare_gray(roi_img)
                    baseline_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    prev_roi_gray = baseline_gray.copy()
                    print(f"[OK] Baseline disimpan pada {baseline_time}")
        elif key == ord('m'):
            if baseline_gray is None:
                print("[WARN] Capture baseline dulu (c).")
            else:
                monitoring = not monitoring
                print(f"[INFO] Monitoring {'ON' if monitoring else 'OFF'}")

        if monitoring and ROI:
            x0, y0, x1, y1 = ROI
            roi_img = frame[y0:y1, x0:x1]
            if roi_img.size == 0:
                cv2.imshow(win_name, display)
                continue

            cur_gray = prepare_gray(roi_img, size=(baseline_gray.shape[1], baseline_gray.shape[0]))

            mot = 0.0
            if prev_roi_gray is not None:
                mot = motion_score(prev_roi_gray, cur_gray)

            diff_pct = percent_diff(baseline_gray, cur_gray)

            persons = 0
            try:
                results = model.predict(source=roi_img, verbose=False, imgsz=320)
                for r in results:
                    if hasattr(r, 'boxes') and r.boxes is not None:
                        cls_ids = r.boxes.cls.cpu().numpy() if hasattr(r.boxes.cls, 'cpu') else np.array([])
                        for cid in cls_ids:
                            name = r.names[int(cid)]
                            if name.lower() in ("person", "people"):
                                persons += 1
            except Exception:
                persons = 0

            info_txt = f"mot:{mot:.3f} diff:{diff_pct:.3f} ppl:{persons}"
            cv2.putText(display, info_txt, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            MOTION_THRESHOLD = 0.03
            DIFF_THRESHOLD = 0.18
            PERSON_THRESHOLD = 1

            triggered = False
            reason = ""
            now_ts = time.time()

            if diff_pct > DIFF_THRESHOLD:
                triggered = True
                reason = f"Significant change vs baseline (diff={diff_pct:.3f})"

            if persons >= PERSON_THRESHOLD and mot > MOTION_THRESHOLD:
                triggered = True
                reason = f"Person detected + motion (ppl={persons}, mot={mot:.3f})"

            if triggered:
                status_text = "!! DICURI !!"
                status_color = (0, 0, 255)
            else:
                status_text = "AMAN"
                status_color = (0, 200, 0)

            if triggered and (now_ts - last_alarm) > alarm_cooldown:
                last_alarm = now_ts
                log_event(reason)
                play_tts()  # lebih cepat karena pakai file cache

            prev_roi_gray = cur_gray.copy()

        cv2.putText(display, status_text, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 3)
        cv2.imshow(win_name, display)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
