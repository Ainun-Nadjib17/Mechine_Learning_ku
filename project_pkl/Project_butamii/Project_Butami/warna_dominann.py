import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Fungsi untuk mencari warna dominan
def get_dominant_colors(image, k=5):
    # Ubah gambar ke array 2D
    pixels = image.reshape((-1, 3))

    # KMeans clustering
    kmeans = KMeans(n_clusters=k, n_init=10)
    kmeans.fit(pixels)

    # Ambil warna cluster
    colors = kmeans.cluster_centers_.astype(int)
    labels = np.bincount(kmeans.labels_)

    # Urutkan warna dari yang paling dominan
    sorted_idx = np.argsort(-labels)
    dominant_colors = colors[sorted_idx]
    color_percentage = labels[sorted_idx] / sum(labels)

    return dominant_colors, color_percentage

# === MAIN PROGRAM ===
# Load gambar
path = "banyakwarna.JPG"  # ganti dengan path gambar lo
image = cv2.imread(path)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Cari warna dominan
dominant_colors, percentages = get_dominant_colors(image, k=5)

# Print hasil
print("Warna dominan (RGB) dan persentasenya:")
for color, p in zip(dominant_colors, percentages):
    print(f"{tuple(color)} - {p*100:.2f}%")

# === Visualisasi ===
plt.figure(figsize=(8, 6))

# Tampilkan gambar asli
plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title("Gambar Asli")
plt.axis("off")

# Tampilkan palet warna
plt.subplot(1, 2, 2)
palette = np.zeros((100, 500, 3), dtype=np.uint8)

start = 0
for color, p in zip(dominant_colors, percentages):
    end = start + int(p * 500)
    palette[:, start:end, :] = color
    start = end

plt.imshow(palette)
plt.title("Palet Warna Dominan")
plt.axis("off")

plt.show()
