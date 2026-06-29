import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture("image/manusiml.mp4")

cv2.namedWindow("Video", cv2.WINDOW_NORMAL)

width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
cv2.resizeWindow("Video", width, height)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)
    human_count = 0

    for box in results[0].boxes:
        if int(box.cls[0]) == 0:
            human_count += 1

    frame = results[0].plot()
    cv2.putText(frame, f"Humans: {human_count}", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Video", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
