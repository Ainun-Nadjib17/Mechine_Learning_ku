import cv2
from ultralytics import YOLO

print("CV2 OK:", cv2.__version__)

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)
    count = 0

    for box in results[0].boxes:
        if int(box.cls[0]) == 0:
            count += 1

    frame = results[0].plot()
    cv2.putText(frame, f"Humans: {count}", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Realtime", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
