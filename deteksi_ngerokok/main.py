import cv2
import mediapipe as mp
import math
import time
import os
import threading
import urllib.request

try:
    import winsound  # Alarm sound, khusus Windows
except ImportError:
    winsound = None

try:
    from ultralytics import YOLO  # Deteksi rokok / asap
except ImportError:
    YOLO = None

# ============================================================
# DETEKSI JARI MENDEKATI BIBIR - OpenCV + MediaPipe
# Simpan sebagai: main.py
#
# Install:
#   pip install opencv-python mediapipe
#
# Jalankan:
#   python main.py
#
# Tombol:
#   Q / ESC = keluar
# ============================================================

# ---------- Pengaturan ----------
CAMERA_INDEX = 0
FRAME_WIDTH = 960
FRAME_HEIGHT = 720

# Jarak normalisasi. Semakin kecil = semakin sensitif.
# Nilai ini membandingkan jarak ujung jari dengan lebar wajah.
TRIGGER_RATIO = 0.23

# Agar status tidak terlalu mudah berubah-ubah.
REQUIRED_FRAMES = 3

# Jika True, tampilkan landmark tangan/wajah.
SHOW_LANDMARKS = True

# ---------- Pengaturan Alarm ----------
ALARM_ENABLED = True      # Nyalakan / matikan alarm
ALARM_BEEP_COUNT = 3      # Jumlah beep per alarm
ALARM_BEEP_FREQ = 1200    # Frekuensi beep (Hz)
ALARM_BEEP_MS = 180       # Durasi tiap beep (ms)
ALARM_COOLDOWN = 2.0      # Jeda antar alarm selama masih terpicu (detik)

# ---------- Pengaturan Deteksi Rokok / Asap ----------
SMOKE_DETECTION_ENABLED = True   # Nyalakan / matikan deteksi rokok
SMOKE_MODEL_URL = "https://huggingface.co/Enos-123/smoking-detection/resolve/main/best.pt"
SMOKE_MODEL_PATH = "best_smoke.pt"
SMOKE_CONFIDENCE = 0.45          # Ambang keyakinan deteksi (0.0 - 1.0)
SMOKE_ALARM_COOLDOWN = 5.0       # Jeda antar alarm rokok (detik)

# ---------- MediaPipe ----------
mp_hands = mp.solutions.hands
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


def distance(p1, p2):
    """Jarak Euclidean antara dua titik."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def lm_to_xy(landmark, width, height):
    """Ubah koordinat landmark MediaPipe menjadi koordinat pixel."""
    return int(landmark.x * width), int(landmark.y * height)


def play_alarm():
    """Bunyikan beep alarm di thread terpisah agar video tidak macet."""
    if not ALARM_ENABLED or winsound is None:
        return

    def _beep():
        try:
            for _ in range(ALARM_BEEP_COUNT):
                winsound.Beep(ALARM_BEEP_FREQ, ALARM_BEEP_MS)
        except Exception:
            pass

    threading.Thread(target=_beep, daemon=True).start()


def download_smoke_model(path, url):
    """Unduh model YOLO deteksi rokok jika belum ada di disk."""
    if os.path.exists(path):
        return True

    print("Mengunduh model deteksi rokok (~40 MB, sekali saja)...")
    try:
        urllib.request.urlretrieve(url, path)
        print("Model rokok tersimpan:", path)
        return True
    except Exception as e:
        print("WARNING: Gagal mengunduh model rokok:", e)
        return False


class SmokeDetector:
    """Deteksi rokok/asap berjalan di thread terpisah agar video tetap lancar."""

    def __init__(self, model, confidence):
        self.model = model
        self.confidence = confidence
        self.latest_boxes = []        # [(x1, y1, x2, y2, label, conf), ...]
        self.lock = threading.Lock()
        self.pending_frame = None
        self.frame_lock = threading.Lock()

        worker = threading.Thread(target=self._loop, daemon=True)
        worker.start()

    def update_frame(self, frame):
        """Kirim frame terbaru ke worker (menimpa frame lama)."""
        with self.frame_lock:
            self.pending_frame = frame.copy()

    def get_boxes(self):
        with self.lock:
            return self.latest_boxes

    def _loop(self):
        while True:
            with self.frame_lock:
                frame = self.pending_frame
                self.pending_frame = None

            if frame is None:
                time.sleep(0.03)
                continue

            try:
                results = self.model.predict(
                    frame,
                    conf=self.confidence,
                    verbose=False
                )

                boxes = []
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        label = self.model.names.get(
                            int(box.cls[0]), "rokok"
                        )
                        conf = float(box.conf[0])
                        boxes.append((x1, y1, x2, y2, label, conf))

                with self.lock:
                    self.latest_boxes = boxes
            except Exception as e:
                print("WARNING: Deteksi rokok gagal:", e)
                time.sleep(1.0)


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

    # Jika CAP_DSHOW tidak cocok di komputer tertentu, coba backend default.
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("ERROR: Kamera tidak bisa dibuka.")
        print("Coba ubah CAMERA_INDEX = 0 menjadi 1 atau 2.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    # ---------- Muat model deteksi rokok ----------
    smoke_detector = None

    if SMOKE_DETECTION_ENABLED:
        if YOLO is None:
            print("WARNING: ultralytics belum terpasang, deteksi rokok mati.")
            print("Install dengan: pip install ultralytics")
        elif download_smoke_model(SMOKE_MODEL_PATH, SMOKE_MODEL_URL):
            try:
                smoke_detector = SmokeDetector(
                    YOLO(SMOKE_MODEL_PATH),
                    SMOKE_CONFIDENCE
                )
                print("Model deteksi rokok siap.")
            except Exception as e:
                print("WARNING: Gagal memuat model rokok:", e)

    triggered_count = 0
    safe_count = 0

    last_trigger_time = 0.0
    last_alarm_time = 0.0
    last_smoke_alarm_time = 0.0
    alert_until = 0.0

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.55,
        min_tracking_confidence=0.55
    ) as hands, mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.55,
        min_tracking_confidence=0.55
    ) as face_mesh:

        while True:
            ok, frame = cap.read()

            if not ok:
                print("ERROR: Gagal membaca frame kamera.")
                break

            # Mirror supaya terasa seperti kamera selfie.
            frame = cv2.flip(frame, 1)

            h, w = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            hand_result = hands.process(rgb)
            face_result = face_mesh.process(rgb)

            # Kirim frame ke detektor rokok (worker thread), ambil hasil
            # deteksi terakhir yang tersedia.
            smoke_boxes = []
            if smoke_detector is not None:
                smoke_detector.update_frame(frame)
                smoke_boxes = smoke_detector.get_boxes()

            finger_point = None
            lip_point = None
            face_width = None

            # ========================================================
            # 1. DETEKSI BIBIR + LEBAR WAJAH
            # ========================================================
            if face_result.multi_face_landmarks:
                face = face_result.multi_face_landmarks[0]

                # MediaPipe Face Mesh:
                # 13 = bibir atas, 14 = bibir bawah
                upper_lip = lm_to_xy(face.landmark[13], w, h)
                lower_lip = lm_to_xy(face.landmark[14], w, h)

                lip_point = (
                    (upper_lip[0] + lower_lip[0]) // 2,
                    (upper_lip[1] + lower_lip[1]) // 2
                )

                # 234 dan 454 kira-kira sisi kiri/kanan wajah.
                face_left = lm_to_xy(face.landmark[234], w, h)
                face_right = lm_to_xy(face.landmark[454], w, h)

                face_width = distance(face_left, face_right)

                if SHOW_LANDMARKS:
                    mp_drawing.draw_landmarks(
                        frame,
                        face,
                        mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing_styles
                        .get_default_face_mesh_contours_style()
                    )

                cv2.circle(frame, lip_point, 6, (255, 0, 0), -1)
                cv2.putText(
                    frame,
                    "BIBIR",
                    (lip_point[0] + 8, lip_point[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 0),
                    2
                )

            # ========================================================
            # 2. DETEKSI UJUNG JARI TELUNJUK
            # ========================================================
            if hand_result.multi_hand_landmarks:
                best_finger = None

                for hand_landmarks in hand_result.multi_hand_landmarks:
                    # Landmark 8 = ujung jari telunjuk.
                    index_tip = lm_to_xy(
                        hand_landmarks.landmark[8], w, h
                    )

                    # Pilih jari yang paling dekat dengan bibir.
                    if lip_point is not None:
                        d = distance(index_tip, lip_point)

                        if best_finger is None or d < best_finger[0]:
                            best_finger = (d, index_tip, hand_landmarks)
                    elif best_finger is None:
                        best_finger = (0, index_tip, hand_landmarks)

                if best_finger is not None:
                    _, finger_point, selected_hand = best_finger

                    if SHOW_LANDMARKS:
                        mp_drawing.draw_landmarks(
                            frame,
                            selected_hand,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing_styles.get_default_hand_landmarks_style(),
                            mp_drawing_styles.get_default_hand_connections_style()
                        )

                    cv2.circle(frame, finger_point, 8, (0, 255, 255), -1)

            # ========================================================
            # 3. DETEKSI ROKOK / ASAP (YOLO di thread terpisah)
            # ========================================================
            smoke_detected = len(smoke_boxes) > 0

            for (x1, y1, x2, y2, label, conf) in smoke_boxes:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(
                    frame,
                    f"{label} {conf:.0%}",
                    (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )

            if smoke_detected and time.time() - last_smoke_alarm_time >= SMOKE_ALARM_COOLDOWN:
                play_alarm()
                last_smoke_alarm_time = time.time()

            # ========================================================
            # 4. HITUNG JARAK JARI -> BIBIR
            # ========================================================
            distance_px = None
            ratio = None
            triggered = False

            if finger_point is not None and lip_point is not None:
                distance_px = distance(finger_point, lip_point)

                if face_width is not None and face_width > 1:
                    ratio = distance_px / face_width

                    # Semakin dekat jari ke bibir, ratio semakin kecil.
                    if ratio <= TRIGGER_RATIO:
                        triggered_count += 1
                        safe_count = 0
                    else:
                        safe_count += 1
                        triggered_count = 0

                    if triggered_count >= REQUIRED_FRAMES:
                        triggered = True
                        alert_until = time.time() + 0.8
                        last_trigger_time = time.time()

                        # Bunyikan alarm (dengan cooldown biar nggak spam).
                        now = time.time()
                        if now - last_alarm_time >= ALARM_COOLDOWN:
                            play_alarm()
                            last_alarm_time = now

                    if safe_count >= REQUIRED_FRAMES:
                        triggered = False

                # Garis dari jari ke bibir.
                cv2.line(
                    frame,
                    finger_point,
                    lip_point,
                    (0, 165, 255),
                    2
                )

            # Status alert dibuat bertahan sebentar agar terlihat jelas.
            if time.time() < alert_until:
                triggered = True

            # ========================================================
            # 5. UI
            # ========================================================
            if distance_px is None:
                jarak_text = "Jari: --"
            else:
                jarak_text = f"Jari: {distance_px:.0f}px"

            if ratio is None:
                ratio_text = "Rasio: --"
            else:
                ratio_text = f"Rasio: {ratio:.2f}"

            status_text = "TERPICU" if triggered else "AMAN"
            rokok_text = "ROKOK: ADA!" if smoke_detected else "Rokok: --"

            # Background panel atas.
            cv2.rectangle(
                frame,
                (0, 0),
                (w, 105),
                (20, 20, 20),
                -1
            )

            # Status.
            alert_active = triggered or smoke_detected
            status_color = (0, 0, 255) if alert_active else (0, 220, 0)

            # Border merah berkedip saat ada alarm.
            if alert_active and int(time.time() * 4) % 2 == 0:
                cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 0, 255), 10)

            cv2.putText(
                frame,
                f"{jarak_text} | {ratio_text} | {rokok_text} | Status: {status_text}",
                (20, 38),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.78,
                (255, 255, 255),
                2
            )

            alert_text = "Tangan terdeteksi - sistem memantau jarak ke bibir"
            if triggered and smoke_detected:
                alert_text = "!!! JARI DI BIBIR + ROKOK TERDETEKSI !!!"
            elif triggered:
                alert_text = "!!! BERHENTI / JAUHKAN JARI DARI MULUT !!!"
            elif smoke_detected:
                alert_text = "!!! ROKOK / ASAP TERDETEKSI !!!"

            cv2.putText(
                frame,
                alert_text,
                (20, 85),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75 if alert_active else 0.55,
                status_color if alert_active else (200, 200, 200),
                2 if alert_active else 1
            )

            # Footer.
            cv2.putText(
                frame,
                "Q / ESC = Keluar",
                (20, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (220, 220, 220),
                1
            )

            cv2.imshow("Sistem Deteksi Jari ke Bibir", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
