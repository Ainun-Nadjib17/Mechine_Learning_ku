import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import tensorflow as tf
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import os

# ================= 1. LOAD MODEL =================
print("⏳ Sedang memuat model AI...")
try:
    # Pastikan file .h5 ada di folder yang sama dengan script ini
    model = tf.keras.models.load_model(
        'fish_freshness_model.h5',
        custom_objects={'preprocess_input': preprocess_input}
    )
    print("✅ Model berhasil dimuat!")
except Exception as e:
    print(f"❌ Gagal memuat model: {e}")
    print("Pastikan file 'fish_freshness_model.h5' ada di folder yang sama dengan script ini.")
    exit()

# Konfigurasi Kelas
class_names = ['C1', 'C2', 'C3']
class_mapping = {
    'C1': 'SEGAR (1-2 Hari) ✅',
    'C2': 'KURANG SEGAR (3-4 Hari) ⚠️',
    'C3': 'BUSUK (5-6 Hari) ❌'
}

# Variabel global untuk menyimpan path gambar
selected_image_path = None

# ================= 2. FUNGSI LOGIKA =================
def select_image():
    global selected_image_path, imgtk
    
    # Buka dialog pilih file
    path = filedialog.askopenfilename(
        title="Pilih Foto Ikan",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
    )
    
    if path:
        selected_image_path = path
        
        # Load gambar untuk ditampilkan di GUI (Resize biar pas di layar)
        img = Image.open(path)
        img = img.resize((300, 300), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(img)
        
        # Update canvas dengan gambar baru
        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        canvas.image = imgtk # Simpan referensi agar tidak di-garbage collect
        
        # Reset label hasil
        result_label.config(text="Silakan klik 'Prediksi Ikan'", fg="gray")

def predict_image():
    global selected_image_path
    
    if not selected_image_path:
        messagebox.showwarning("Peringatan", "Pilih gambar ikan dulu bro!")
        return
    
    # Tampilkan status loading
    result_label.config(text="🔄 Sedang menganalisis...", fg="blue")
    root.update() # Refresh UI
    
    try:
        # 1. Preprocessing gambar (Ukuran 128x128 sesuai training)
        img = tf.keras.utils.load_img(selected_image_path, target_size=(128, 128))
        img_array = tf.keras.utils.img_to_array(img)
        img_array = tf.expand_dims(img_array, 0) # Tambah dimensi batch
        
        # 2. Prediksi
        predictions = model.predict(img_array, verbose=0)
        
        # 🔑 PENTING: Hapus tf.nn.softmax! Model sudah output softmax.
        score = predictions[0] 
        
        pred_idx = np.argmax(score)
        pred_class = class_names[pred_idx]
        confidence = 100 * np.max(score)
        
        # 3. Tampilkan Hasil
        status_text = class_mapping[pred_class]
        result_text = f"Kelas: {pred_class}\nStatus: {status_text}\nKeyakinan: {confidence:.2f}%"
        
        # Ganti warna teks berdasarkan hasil
        if pred_class == 'C1':
            color = "green"
        elif pred_class == 'C2':
            color = "orange"
        else:
            color = "red"
            
        result_label.config(text=result_text, fg=color, font=("Arial", 12, "bold"))
        
    except Exception as e:
        messagebox.showerror("Error", f"Gagal memproses gambar:\n{e}")

# ================= 3. MEMBUAT TAMPILAN GUI (TKINTER) =================
root = tk.Tk()
root.title(" Aplikasi Deteksi Kesegaran Ikan")
root.geometry("450x600")
root.configure(bg="#f0f0f0")

# Judul
title_label = tk.Label(root, text="Deteksi Kesegaran Ikan (CNN)", font=("Arial", 16, "bold"), bg="#f0f0f0", pady=10)
title_label.pack()

# Area Gambar (Canvas)
canvas_frame = tk.Frame(root, bg="white", padx=5, pady=5)
canvas_frame.pack()

canvas = tk.Canvas(canvas_frame, width=300, height=300, bg="white")
canvas.pack()
canvas.create_text(150, 150, text="Belum ada gambar", fill="gray", font=("Arial", 12))

# Tombol Upload
btn_upload = tk.Button(root, text=" Pilih Gambar", command=select_image, 
                       font=("Arial", 12), bg="#4CAF50", fg="white", padx=20, pady=5, cursor="hand2")
btn_upload.pack(pady=10)

# Tombol Prediksi
btn_predict = tk.Button(root, text="🔍 Prediksi Ikan", command=predict_image, 
                        font=("Arial", 12), bg="#2196F3", fg="white", padx=20, pady=5, cursor="hand2")
btn_predict.pack(pady=5)

# Label Hasil
result_label = tk.Label(root, text="Silakan pilih gambar...", font=("Arial", 12), bg="#f0f0f0", pady=20)
result_label.pack()

# Footer
footer_label = tk.Label(root, text="Powered by MobileNetV2 CNN", font=("Arial", 8), bg="#f0f0f0", fg="gray")
footer_label.pack(side=tk.BOTTOM, pady=10)

# Jalankan Aplikasi
if __name__ == "__main__":
    root.mainloop()