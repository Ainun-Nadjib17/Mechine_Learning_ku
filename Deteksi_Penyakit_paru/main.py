
import tensorflow as tf
import numpy as np
from PIL import Image
import os
import tkinter as tk
from tkinter import filedialog
import cv2

# ============================================================
# LUNGVISION AI
# Chest X-Ray Classification
# NORMAL vs PNEUMONIA
# ============================================================

MODEL_PATH = "lungvision_final.keras"
IMG_SIZE = (224, 224)

# ------------------------------------------------------------
# 1. Load model
# ------------------------------------------------------------

print("Loading LungVision AI model...")

model = tf.keras.models.load_model(MODEL_PATH)

print("Model berhasil dimuat!")
print()


# ------------------------------------------------------------
# 2. Fungsi preprocessing
# ------------------------------------------------------------

def preprocess_image(image_path):

    image = Image.open(image_path).convert("RGB")

    image = image.resize(IMG_SIZE)

    image_array = np.array(image, dtype=np.float32)

    image_array = np.expand_dims(image_array, axis=0)

    return image_array


# ------------------------------------------------------------
# 3. Fungsi prediksi
# ------------------------------------------------------------

def predict(image_path):

    if not os.path.exists(image_path):
        print("File tidak ditemukan!")
        return

    image = preprocess_image(image_path)

    prediction = model.predict(image, verbose=0)

    pneumonia_probability = float(prediction[0][0])

    normal_probability = 1 - pneumonia_probability

    threshold = 0.5

    if pneumonia_probability >= threshold:
        result = "PNEUMONIA"
        confidence = pneumonia_probability
    else:
        result = "NORMAL"
        confidence = normal_probability

    return {
        "prediction": result,
        "confidence": confidence,
        "normal_probability": normal_probability,
        "pneumonia_probability": pneumonia_probability
    }


# ------------------------------------------------------------
# 4. File picker
# ------------------------------------------------------------

def select_xray():

    root = tk.Tk()
    root.withdraw()

    image_path = filedialog.askopenfilename(
        title="Pilih Foto X-Ray",
        filetypes=[
            ("Image Files", "*.jpg *.jpeg *.png *.bmp"),
            ("JPG Files", "*.jpg *.jpeg"),
            ("PNG Files", "*.png"),
            ("All Files", "*.*")
        ]
    )

    root.destroy()

    return image_path


# ------------------------------------------------------------
# 5. Tampilan X-Ray + Hasil
# ------------------------------------------------------------

def show_result(image_path, result):

    image = cv2.imread(image_path)

    if image is None:
        print("Gambar tidak dapat dibuka.")
        return

    # --------------------------------------------------------
    # Resize X-Ray
    # --------------------------------------------------------

    max_width = 600
    max_height = 450

    height, width = image.shape[:2]

    scale = min(
        max_width / width,
        max_height / height,
        1
    )

    if scale < 1:

        new_width = int(width * scale)
        new_height = int(height * scale)

        image = cv2.resize(
            image,
            (new_width, new_height)
        )

    image_height, image_width = image.shape[:2]

    # --------------------------------------------------------
    # Panel hasil
    # --------------------------------------------------------

    panel_width = 400

    panel = np.zeros(
        (image_height, panel_width, 3),
        dtype=np.uint8
    )

    # Background panel
    panel[:] = (30, 30, 30)

    # --------------------------------------------------------
    # Text
    # --------------------------------------------------------

    prediction = result["prediction"]
    confidence = result["confidence"] * 100

    normal_probability = result["normal_probability"] * 100
    pneumonia_probability = result["pneumonia_probability"] * 100

    font = cv2.FONT_HERSHEY_SIMPLEX

    # Judul
    cv2.putText(
        panel,
        "LUNGVISION AI",
        (30, 55),
        font,
        1.0,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        panel,
        "Chest X-Ray Analysis",
        (30, 90),
        font,
        0.55,
        (180, 180, 180),
        1,
        cv2.LINE_AA
    )

    # Garis
    cv2.line(
        panel,
        (30, 115),
        (panel_width - 30, 115),
        (100, 100, 100),
        1
    )

    # Prediction
    cv2.putText(
        panel,
        "PREDICTION",
        (30, 165),
        font,
        0.55,
        (180, 180, 180),
        1,
        cv2.LINE_AA
    )

    cv2.putText(
        panel,
        prediction,
        (30, 215),
        font,
        1.2,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    # Confidence
    cv2.putText(
        panel,
        "CONFIDENCE",
        (30, 270),
        font,
        0.55,
        (180, 180, 180),
        1,
        cv2.LINE_AA
    )

    cv2.putText(
        panel,
        f"{confidence:.2f}%",
        (30, 315),
        font,
        1.0,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    # Probabilitas
    cv2.putText(
        panel,
        f"NORMAL      {normal_probability:.2f}%",
        (30, 365),
        font,
        0.55,
        (220, 220, 220),
        1,
        cv2.LINE_AA
    )

    cv2.putText(
        panel,
        f"PNEUMONIA   {pneumonia_probability:.2f}%",
        (30, 400),
        font,
        0.55,
        (220, 220, 220),
        1,
        cv2.LINE_AA
    )

    cv2.putText(
        panel,
        "Press any key to close",
        (30, image_height - 25),
        font,
        0.45,
        (150, 150, 150),
        1,
        cv2.LINE_AA
    )

    # --------------------------------------------------------
    # Gabungkan gambar + panel
    # --------------------------------------------------------

    combined = np.hstack((image, panel))

    # --------------------------------------------------------
    # Tampilkan
    # --------------------------------------------------------

    cv2.imshow(
        "LungVision AI",
        combined
    )

    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ------------------------------------------------------------
# 6. Jalankan program
# ------------------------------------------------------------

if __name__ == "__main__":

    print("==============================================")
    print("             LUNGVISION AI")
    print("      Chest X-Ray Classification")
    print("==============================================")
    print()

    print("Silakan pilih foto X-Ray dari File Manager...")

    image_path = select_xray()

    if not image_path:

        print("Tidak ada gambar yang dipilih.")

    else:

        print()
        print(f"File dipilih : {image_path}")
        print("Menganalisis gambar...")

        result = predict(image_path)

        if result is not None:

            print()
            print("Prediction :", result["prediction"])
            print(
                "Confidence : "
                f"{result['confidence'] * 100:.2f}%"
            )

            show_result(
                image_path,
                result
            )
