from ultralytics import YOLO
import cv2

# Load model
model = YOLO("best.pt")

# Gambar yang mau dites
image_path = "test3.jpg"

# Jalankan deteksi
results = model(image_path)

# Ambil hasil
for result in results:
    boxes = result.boxes

    for box in boxes:
        # koordinat bounding box
        x1, y1, x2, y2 = box.xyxy[0]

        # confidence
        conf = float(box.conf[0])

        # class id
        cls = int(box.cls[0])

        # nama kelas
        label = model.names[cls]

        print(
            f"Penyakit: {label} | Confidence: {conf:.2f}"
        )

    # tampilkan hasil
    annotated = result.plot()

    cv2.imshow(
        "Tomato Disease Deteksi",
        annotated
    )

    cv2.waitKey(0)

cv2.destroyAllWindows()