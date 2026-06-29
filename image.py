import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

img = cv2.imread("image/manusia_ML.jpg")
results = model(img)

count = 0
for r in results:
    for box in r.boxes:
        cls = int(box.cls[0])
        if cls == 0:  # class 0 = person
            count += 1

print("Jumlah manusia:", count)

annotated = results[0].plot()

cv2.putText(
    annotated,
    f"Total Manusia: {count}",
    (20, 40),
    cv2.FONT_HERSHEY_SIMPLEX,
    1,
    (0, 255, 0),
    2
)

cv2.imshow("Human Detection", annotated)
cv2.waitKey(0)
