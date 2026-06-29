import cv2
import numpy as np
import tensorflow as tf

model = tf.keras.models.load_model("model.h5")
labels = ["mentah", "matang", "terlalu_matang"]

# ==== LOAD IMAGE ====
orig_img = cv2.imread("test11.jpg")

# ==== PREPROCESS (TETAP) ====
img = cv2.resize(orig_img, (128,128))
img = img / 255.0
img = np.expand_dims(img, axis=0)

pred = model.predict(img)
hasil = labels[np.argmax(pred)]

# ==== WINDOW RESPONSIF ====
cv2.namedWindow("Klasifikasi Buah", cv2.WINDOW_NORMAL)

# ==== TRACKBAR ZOOM ====
def nothing(x):
    pass

cv2.createTrackbar("Zoom %", "Klasifikasi Buah", 100, 200, nothing)

while True:
    zoom = cv2.getTrackbarPos("Zoom %", "Klasifikasi Buah")
    zoom = max(50, zoom)
    scale = zoom / 100

    h, w, _ = orig_img.shape
    frame = cv2.resize(orig_img, (int(w*scale), int(h*scale)))

    # ==== BORDER TIPIS ====
    cv2.rectangle(
        frame,
        (2, 2),
        (frame.shape[1]-2, frame.shape[0]-2),
        (0, 200, 0),
        2
    )

    # ==== INFO PANEL ====
    panel_h = 45
    overlay = frame.copy()
    cv2.rectangle(overlay, (0,0), (frame.shape[1], panel_h), (0,0,0), -1)
    frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)

    # ==== TEXT ====
    cv2.putText(
        frame,
        f"Hasil: {hasil}",
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0,255,0),
        2
    )

    cv2.imshow("Klasifikasi Buah", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
