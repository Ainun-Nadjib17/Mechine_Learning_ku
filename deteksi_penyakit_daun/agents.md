# AGENTS.md

# 🍅 Sistem Deteksi Penyakit Daun Tomat Berbasis AI

## Deskripsi Proyek

Proyek ini merupakan website berbasis Artificial Intelligence yang digunakan untuk mendeteksi penyakit pada daun tomat menggunakan model YOLOv8 hasil pelatihan sendiri.

Website ini tidak hanya menampilkan hasil deteksi, tetapi juga memberikan informasi mengenai penyakit, penyebab, gejala, pencegahan, serta penanganan berdasarkan hasil deteksi.

Website dibuat sebagai media edukasi sekaligus alat bantu identifikasi penyakit daun tomat.

---

# Tujuan

- Mendeteksi penyakit daun tomat dari gambar yang diunggah pengguna.
- Menampilkan nama penyakit dan tingkat kepercayaan (confidence).
- Memberikan informasi lengkap mengenai penyakit.
- Memberikan rekomendasi penanganan.
- Memiliki tampilan modern, sederhana, dan mudah digunakan.

---

# Teknologi

Backend

- Python
- Flask
- Ultralytics YOLOv8
- OpenCV

Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap 5

Model AI

- YOLOv8
- best.pt

---

# Struktur Folder

```
tomato-ai/

│
├── app.py
├── best.pt
├── requirements.txt
├── README.md
├── AGENTS.md
│
├── database/
│     └── disease_info.json
│
├── static/
│     ├── css/
│     ├── js/
│     ├── images/
│     ├── uploads/
│     └── results/
│
├── templates/
│     ├── layout.html
│     ├── index.html
│     ├── tentang.html
│     ├── deteksi.html
│     ├── penyakit.html
│     ├── detail_penyakit.html
│     └── kontak.html
│
└── utils/
      └── detector.py
```

---

# Halaman Website

## Beranda

Menampilkan

- Hero Section
- Penjelasan singkat sistem
- Statistik model
- Tombol Mulai Deteksi

---

## Tentang

Berisi

- Latar belakang
- Tujuan sistem
- Penjelasan Computer Vision
- Penjelasan YOLOv8
- Dataset yang digunakan

---

## Deteksi Penyakit

Pengguna dapat

- Mengunggah gambar daun tomat
- Melakukan deteksi AI

Hasil yang ditampilkan

- Gambar hasil deteksi
- Nama penyakit
- Confidence
- Informasi penyakit

---

## Informasi Penyakit

Berisi daftar seluruh penyakit yang dapat dideteksi.

Setiap halaman penyakit berisi

- Nama penyakit
- Nama ilmiah
- Penyebab
- Gejala
- Pencegahan
- Penanganan
- Referensi

---

## Kontak

Berisi

- Nama pengembang
- Email
- GitHub
- LinkedIn

---

# Alur Sistem

Pengguna

↓

Upload Gambar

↓

Model YOLOv8 (best.pt)

↓

Hasil Deteksi

↓

Membaca database disease_info.json

↓

Menampilkan informasi penyakit

↓

Website

---

# Database Penyakit

Seluruh informasi penyakit disimpan pada

database/disease_info.json

Setiap penyakit memiliki

- nama
- nama ilmiah
- deskripsi
- penyebab
- gejala
- pencegahan
- penanganan
- referensi

Jangan menuliskan informasi penyakit secara langsung di dalam file Python.

Selalu membaca data dari JSON.

---

# Aturan Pengembangan

Selalu

- Gunakan model best.pt.
- Pisahkan kode backend dan frontend.
- Gunakan struktur folder yang rapi.
- Gunakan Bootstrap agar responsif.
- Gunakan Bahasa Indonesia pada seluruh tampilan website.
- Gunakan desain modern dan sederhana.

Jangan

- Menambahkan sistem login.
- Menambahkan dashboard admin.
- Menambahkan database pengguna.
- Mengubah model AI.
- Melatih ulang model dari website.

---

# Desain Website

Tema

Modern

Minimalis

Responsif

Warna

Hijau Daun

Putih

Merah Tomat sebagai aksen

Border Radius

16px

Shadow

Soft

Animasi

Halus

---

# Target Pengguna

- Mahasiswa
- Petani
- Penyuluh Pertanian
- Peneliti

---

# Tujuan Akhir

Website ini harus terlihat seperti aplikasi AI profesional yang mudah digunakan.

Fokus utama

- Kemudahan penggunaan
- Tampilan modern
- Hasil deteksi yang akurat
- Informasi penyakit yang lengkap
- Kode yang rapi dan mudah dikembangkan