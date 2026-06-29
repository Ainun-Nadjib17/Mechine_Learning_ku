import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# ==== 1. DETEKSI WARNA DOMINAN ====
def get_dominant_colors(image, k=3):
    # ubah ke array 2D
    pixels = image.reshape((-1, 3))
    
    # clustering dengan KMeans
    kmeans = KMeans(n_clusters=k, n_init=10)
    kmeans.fit(pixels)
    
    colors = kmeans.cluster_centers_.astype(int)  # warna dominan (RGB)
    return colors

# ==== 2. COLOR PICKER ====
clicked = False
r = g = b = xpos = ypos = 0

def pick_color(event, x, y, flags, param):
    global clicked, r, g, b, xpos, ypos
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked = True
        xpos, ypos = x, y
        b, g, r = image[y, x]
        b, g, r = int(b), int(g), int(r)

# Load gambar
path = "banyakwarna.JPG"   # ganti dengan file gambar lo
image = cv2.imread(path)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Cari warna dominan
colors = get_dominant_colors(image, k=5)
print("Warna dominan (RGB):")
for i, c in enumerate(colors):
    print(f"{i+1}. {tuple(c)}")

# Tampilkan gambar untuk color picker
cv2.imshow("Image", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
cv2.setMouseCallback("Image", pick_color)

while True:
    cv2.imshow("Image", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if clicked:
        # bikin tampilan warna yang diklik
        color_img = np.zeros((100, 300, 3), np.uint8)
        color_img[:] = [b, g, r]
        
        text = f"RGB: ({r}, {g}, {b})"
        cv2.putText(color_img, text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255-r, 255-g, 255-b), 2, cv2.LINE_AA)
        
        cv2.imshow("Picked Color", color_img)
        clicked = False
    
    if cv2.waitKey(20) & 0xFF == 27:  # ESC untuk keluar
        break

cv2.destroyAllWindows()
import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# ==== 1. DETEKSI WARNA DOMINAN ====
def get_dominant_colors(image, k=3):
    # ubah ke array 2D
    pixels = image.reshape((-1, 3))
    
    # clustering dengan KMeans
    kmeans = KMeans(n_clusters=k, n_init=10)
    kmeans.fit(pixels)
    
    colors = kmeans.cluster_centers_.astype(int)  # warna dominan (RGB)
    return colors

# ==== 2. COLOR PICKER ====
clicked = False
r = g = b = xpos = ypos = 0

def pick_color(event, x, y, flags, param):
    global clicked, r, g, b, xpos, ypos
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked = True
        xpos, ypos = x, y
        b, g, r = image[y, x]
        b, g, r = int(b), int(g), int(r)

# Load gambar
path = "gambar.jpg"   # ganti dengan file gambar lo
image = cv2.imread(path)
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Cari warna dominan
colors = get_dominant_colors(image, k=5)
print("Warna dominan (RGB):")
for i, c in enumerate(colors):
    print(f"{i+1}. {tuple(c)}")

# Tampilkan gambar untuk color picker
cv2.imshow("Image", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
cv2.setMouseCallback("Image", pick_color)

while True:
    cv2.imshow("Image", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if clicked:
        # bikin tampilan warna yang diklik
        color_img = np.zeros((100, 300, 3), np.uint8)
        color_img[:] = [b, g, r]
        
        text = f"RGB: ({r}, {g}, {b})"
        cv2.putText(color_img, text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255-r, 255-g, 255-b), 2, cv2.LINE_AA)
        
        cv2.imshow("Picked Color", color_img)
        clicked = False
    
    if cv2.waitKey(20) & 0xFF == 27:  # ESC untuk keluar
        break

cv2.destroyAllWindows()
