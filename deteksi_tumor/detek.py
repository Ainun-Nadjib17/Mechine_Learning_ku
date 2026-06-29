from tensorflow.keras.models import load_model
import numpy as np
from tensorflow.keras.preprocessing import image
from tkinter import Tk, filedialog
import matplotlib.pyplot as plt
import cv2

# Load model
model = load_model("brain_tumor_model.h5")
classes = ['glioma', 'meningioma', 'notumor', 'pituitary']

# ===============================
# PILIH MODE
# ===============================

print("=== PILIH MODE ===")
print("1. Tampilkan gambar + prediksi")
print("2. Langsung tampil grafik")

mode = input("Pilih mode (1 / 2): ")

# ===============================
# FUNGSI PREDIKSI
# ===============================

def run_prediction(title):

    root = Tk()
    root.withdraw()

    file_paths = filedialog.askopenfilenames(
        title=title,
        filetypes=[("Image files","*.jpg *.jpeg *.png")]
    )

    if not file_paths:
        return None, None

    confidences = []
    predictions = []

    for img_path in file_paths:

        img = image.load_img(img_path, target_size=(224,224))
        img_array = image.img_to_array(img)/255.0
        img_array = np.expand_dims(img_array, axis=0)

        pred = model.predict(img_array, verbose=0)

        predicted_class = classes[np.argmax(pred)]
        confidence = float(np.max(pred))*100

        predictions.append(predicted_class)
        confidences.append(confidence)

        # MODE 1 → tampil gambar
        if mode == "1":

            original = cv2.imread(img_path)

            plt.figure(figsize=(5,5))
            plt.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
            plt.axis("off")
            plt.title(f"{predicted_class} ({confidence:.2f}%)")
            plt.show()

    avg_conf = np.mean(confidences)

    final_class = max(set(predictions), key=predictions.count)

    return final_class, avg_conf


# ===============================
# JALANKAN 4 PREDIKSI
# ===============================

labels = []
values = []

for i in range(1,5):

    tumor, conf = run_prediction(f"Pilih gambar untuk Prediksi {i}")

    if tumor:

        print(f"Prediksi {i}: {tumor} ({conf:.2f}%)")

        labels.append(f"P{i}\n{tumor}")
        values.append(conf)


# ===============================
# GRAFIK BATANG
# ===============================

plt.figure(figsize=(8,5))

plt.bar(labels, values)

plt.title("Statistik Prediksi Tumor Otak")
plt.xlabel("Prediksi")
plt.ylabel("Confidence (%)")

plt.ylim(0,100)

plt.grid(axis="y")

plt.show()