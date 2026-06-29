import cv2
import numpy as np
import glob
from ultralytics import YOLO

# --- Parameters ---
CONF_THRESH = 0.25
IOU_THRESH = 0.45
WEBCAM_IDX = 0

# --- Checkerboard parameters ---
checkerboard = (9, 6)        # jumlah inner corners (bukan jumlah kotak)
square_size = 25.0           # ukuran kotak dalam mm

# ====== STEP 1: Kalibrasi Kamera ======
print(">> [INFO] Mulai kalibrasi kamera pakai checkerboard...")

# Persiapan array 3D untuk titik checkerboard di dunia nyata
objp = np.zeros((checkerboard[0] * checkerboard[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:checkerboard[0], 0:checkerboard[1]].T.reshape(-1, 2)
objp *= square_size

objpoints = []  # 3D point
imgpoints = []  # 2D point
all_scales = []

images = glob.glob("calibration_images/*.jpg")  # folder foto checkerboard

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, corners = cv2.findChessboardCorners(gray, checkerboard, None)
    if ret:
        objpoints.append(objp)
        imgpoints.append(corners)

        # hitung jarak pixel antar sudut di 1 baris checkerboard
        px_dist = np.linalg.norm(corners[0][0] - corners[checkerboard[0]-1][0])
        mm_dist = (checkerboard[0]-1) * square_size
        mm_per_px = mm_dist / px_dist
        all_scales.append(mm_per_px)

        cv2.drawChessboardCorners(img, checkerboard, corners, ret)
        cv2.imshow('Checkerboard', img)
        cv2.waitKey(200)

cv2.destroyAllWindows()

# hitung kalibrasi kamera
if len(objpoints) > 0:
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )
    print("Camera matrix:\n", camera_matrix)
    print("Distortion coefficients:\n", dist_coeffs)

# Skala px → mm hasil rata-rata
if all_scales:
    MM_PER_PX = np.mean(all_scales)
    print(f"\n>> [INFO] Skala terhitung otomatis: {MM_PER_PX:.4f} mm/px")
else:
    print("\n[WARNING] Checkerboard tidak terdeteksi, fallback ke default 0.264 mm/px")
    MM_PER_PX = 0.264

# ====== STEP 2: YOLO Detection ======
print("\n>> [INFO] Memuat model YOLOv8 (ultralytics)...")
model = YOLO("yolov8s.pt")   # otomatis download model kalau belum ada

cap = cv2.VideoCapture(WEBCAM_IDX)
cv2.namedWindow("Deteksi Diameter & Nama (mm)")

print("Tekan 'q' untuk keluar.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Gagal membaca frame dari webcam.")
        break

    h, w = frame.shape[:2]

    # YOLO inference
    results = model(frame, conf=CONF_THRESH, iou=IOU_THRESH)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].item()
            cls = int(box.cls[0].item())

            label = model.names[cls] if cls < len(model.names) else str(cls)

            bbox_w = x2 - x1
            bbox_h = y2 - y1
            diameter_px = max(bbox_w, bbox_h)
            diameter_mm = diameter_px * MM_PER_PX
            diameter_text = f"Diameter: {diameter_mm:.1f} mm"

            # draw box & label
            color = (0, 255, 0)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            txt = f"{label} | {diameter_text}"
            (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (int(x1), int(y1 - th - 8)), (int(x1 + tw + 4), int(y1)), color, -1)
            cv2.putText(frame, txt, (int(x1 + 2), int(y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)

    # tampilkan skala px→mm
    cv2.putText(frame, f"Skala: {MM_PER_PX:.4f} mm/px", (10, h-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    cv2.imshow("Deteksi Diameter & Nama (mm)", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
