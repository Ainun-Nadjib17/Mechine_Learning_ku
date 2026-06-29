import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Fungsi untuk deteksi banyak warna
def detect_colors(image, k=8):
    # Ubah gambar ke array 2D
    pixels = image.reshape((-1, 3))

    # Clustering warna
    kmeans = KMeans(n_clusters=k, n_init=10)
    kmeans.fit(pixels)

    # Ambil warna cluster
    colors = kmeans.cluster_centers_.astype(int)
    labels = np.bincount(kmeans.labels_)

    # Urutkan dari warna paling banyak
    sorted_idx = np.argsort(-labels)
    detected_colors = colors[sorted_idx]
    color_percentage = labels[sorted_idx] / sum(labels)

    return detected_colors, color_percentage

# === MAIN PROGRAM ===
# Load gambar
path = "banyakwarna.JPG"  # ganti dengan path gambar lo
image = cv2.imread(path)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Deteksi banyak warna
detected_colors, percentages = detect_colors(image, k=8)

# Print hasil
print("Daftar warna dalam gambar (RGB) dan persentasenya:")
for color, p in zip(detected_colors, percentages):
    print(f"{tuple(color)} - {p*100:.2f}%")

# === Visualisasi ===
plt.figure(figsize=(12, 6))

# Tampilkan gambar asli
plt.subplot(1, 3, 1)
plt.imshow(image)
plt.title("Gambar Asli")
plt.axis("off")

# Tampilkan palet warna (bar)
plt.subplot(1, 3, 2)
palette = np.zeros((100, 500, 3), dtype=np.uint8)
start = 0
for color, p in zip(detected_colors, percentages):
    end = start + int(p * 500)
    palette[:, start:end, :] = color
    start = end
plt.imshow(palette)
plt.title("Palet Warna")
plt.axis("off")

# Tampilkan pie chart
plt.subplot(1, 3, 3)
hex_colors = ['#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2]) for c in detected_colors]
plt.pie(percentages, labels=hex_colors, colors=hex_colors, autopct='%1.1f%%')
plt.title("Distribusi Warna")

plt.tight_layout()
plt.show()
