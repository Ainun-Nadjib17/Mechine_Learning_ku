import os
import cv2
from ultralytics import YOLO


class TomatoDetector:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, "best.pt")
        self.model = YOLO(model_path)
        self.results_dir = os.path.join(base_dir, "static", "results")
        os.makedirs(self.results_dir, exist_ok=True)

    def detect(self, image_path):
        results = self.model(image_path)
        detections = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = self.model.names[cls]
                detections.append({
                    "class_name": label,
                    "confidence": round(conf * 100, 2),
                    "bbox": [x1, y1, x2, y2],
                })

            annotated = result.plot()
            filename = "result_" + os.path.basename(image_path)
            result_path = os.path.join(self.results_dir, filename)
            cv2.imwrite(result_path, annotated)

        return detections, filename

    def get_model_info(self):
        return {
            "total_classes": len(self.model.names),
            "model_name": "YOLOv8",
            "class_names": self.model.names,
        }
