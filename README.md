# Event Visitor Counter (AI Body Detection & Real-time Dashboard)

Sistem penghitung jumlah pengunjung acara (event) secara *real-time* berbasis **YOLOv8** (Computer Vision), **FastAPI** (Backend REST & WebSockets), dan **Vanilla JS/CSS** (Live Dashboard & Multi-Day Analytics). 

Sistem ini didesain fleksibel untuk menghitung pengunjung melalui beberapa kamera entry (masuk) dan exit (keluar), baik di LAN lokal yang sama maupun terdistribusi di beberapa PC terpisah, serta mendukung **Event Multi-Hari (3-Day Event)** dengan fitur **Auto-Reset Harian** dan **Halaman Laporan Analytics**.

---

## Daftar Isi

1. [Fitur Utama](#fitur-utama)
2. [Prasyarat Sistem](#prasyarat-sistem)
3. [Instalasi & Setup](#instalasi--setup)
4. [Panduan Menjalankan Aplikasi](#panduan-menjalankan-aplikasi)
   - [Langkah 1: Menjalankan Backend Server & Dashboard](#langkah-1-menjalankan-backend-server--dashboard)
   - [Langkah 2: Menjalankan Kamera AI (Camera Runner)](#langkah-2-menjalankan-kamera-ai-camera-runner)
   - [Langkah 3: Akses Halaman Analytics & Histori Multi-Hari](#langkah-3-akses-halaman-analytics--histori-multi-hari)
   - [Langkah 4 (Opsional): Simulasi Pengunjung](#langkah-4-opsional-simulasi-pengunjung-tanpa-kamera)
   - [Langkah 5: Mereset Angka Hitungan Pengunjung](#langkah-5-mereset-angka-hitungan-pengunjung)
5. [Pengaturan Multi-PC / Jaringan Terpisah](#pengaturan-multi-pc--jaringan-terpisah)
6. [Pengujian (Testing)](#pengujian-testing)
7. [Struktur Proyek](#struktur-proyek)

---

## Fitur Utama

- **Live Counter Real-Time**: WebSocket update instan saat ada orang melewati garis hitung.
- **Pencatatan Multi-Hari (Auto-Reset Harian)**: Mendukung event yang berlangsung selama beberapa hari (contoh: 3 hari). Counter harian otomatis di-reset ke `0` setiap awal hari baru, sementara data histori hari sebelumnya tetap tersimpan utuh di database.
- **Halaman Analytics & Histori Event (`analytics.html`)**: Halaman khusus laporan performa event multi-hari yang bersih dan profesional (tanpa emoji, mengacu pedoman [`DESIGN.md`](DESIGN.md)):
  - **Key Metrics**: Total Pengunjung Akumulasi Seluruh Hari, Jam Paling Ramai (Akumulasi), dan Hari Teramai.
  - **Tabel Breakdown Harian**: Rincian Hari ke-, Tanggal, Total Masuk, Total Keluar, dan Puncak Pengunjung Bersamaan (*Peak Inside*).
  - **Grafik Analisis (Chart.js)**: Bar chart perbandingan pengunjung antar-hari & Line chart distribusi jam kedatangan.
- **Zona Waktu Presisi (WIB / GMT+7)**: Semua pencatatan log dan grafik jam keramaian mengikuti waktu lokal Indonesia WIB secara akurat.
- **Monitoring Status & Peran Kamera**: Section khusus di Dashboard untuk mengecek berapa kamera yang terhubung (Connected / Standby), peran masing-masing kamera (MASUK vs KELUAR), dan jumlah hitungan per kamera.
- **Reset Hitungan Real-Time**: Tombol reset di Dashboard & API `POST /api/events/{id}/reset` untuk mengosongkan angka hitungan dan grafik tren kapan saja secara instan di seluruh perangkat tersambung.
- **Deteksi AI Presisi (YOLOv8)**: Tracking objek orang dengan algoritma Line Crossing Counter.
- **Dukungan Multi-Kamera**: Mendukung pemetaan peran kamera (Entry 1-2, Exit 3-7).

---

## Prasyarat Sistem

- **Python**: Versi 3.9 atau lebih baru.
- **Hardware Kamera**: Webcam USB, IP Camera RTSP, atau file video.
- **Model YOLO**: Model pretrained `yolov8n.pt` (otomatis terunduh atau sudah tersedia di root direktori).

---

## Instalasi & Setup

1. **Clone / Buka Direktori Proyek**
   ```bash
   cd c:\visitor-counter
   ```

2. **Buat & Aktifkan Virtual Environment** (Rekomendasi)
   - Windows (PowerShell / CMD):
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Dependensi**
   ```bash
   pip install -r requirements.txt
   ```

---

## Panduan Menjalankan Aplikasi

### Langkah 1: Menjalankan Backend Server & Dashboard

Jalankan FastAPI server menggunakan Uvicorn dengan flag `--reload`. Server ini akan mengelola database SQLite, WebSocket real-time, API REST, dan menyajikan dashboard frontend.

```bash
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

- **Live Dashboard**: Buka browser di [http://localhost:8000](http://localhost:8000)
- **Halaman Analytics**: Buka browser di [http://localhost:8000/analytics.html](http://localhost:8000/analytics.html)
- **API Documentation (Swagger)**: Buka [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Langkah 2: Menjalankan Kamera AI (Camera Runner)

Buka terminal **baru** (dengan virtual environment aktif) untuk menjalankan skrip deteksi kamera:

#### A. Menjalankan dengan Webcam Laptop / USB Default (Camera ID #1 - Entry)
```bash
python camera_runner.py --camera-id 1 --source 0
```

#### B. Menjalankan dengan IP Camera (RTSP Stream) atau File Video

> **Catatan:** URL `rtsp://admin:password@192.168.1.50:554/stream` di bawah adalah **contoh placeholder**. Ganti dengan IP address, username, password, dan stream path asli dari IP Camera Anda.

```bash
# Menggunakan RTSP Stream (Ganti IP & kredensial sesuai kamera Anda)
python camera_runner.py --camera-id 1 --source "rtsp://admin:password@192.168.1.50:554/stream"

# Menggunakan File Video Demo (.mp4 / .avi)
python camera_runner.py --camera-id 1 --source "video_sample.mp4"
```

#### C. Pengaturan Garis Penyeberangan (Line Crossing Options)
- **Kamera Pintu Keluar (Camera ID #3 s/d #7)**:
  ```bash
  python camera_runner.py --camera-id 3 --source 0
  ```
- **Ubah Orientasi & Posisi Garis Deteksi**:
  ```bash
  # Garis Vertikal di Tengah Layar (posisi 0.5)
  python camera_runner.py --camera-id 1 --line-orientation vertical --line-position 0.5

  # Garis Kustom dengan koordinat (x1, y1, x2, y2)
  python camera_runner.py --camera-id 1 --line-coords "100,200,500,200"
  ```
- **Menjalankan Tanpa Jendela Display OpenCV (Headless/Server Mode)**:
  ```bash
  python camera_runner.py --camera-id 1 --source 0 --no-window
  ```

---

### Langkah 3: Akses Halaman Analytics & Histori Multi-Hari

Untuk melihat laporan analisis akumulasi event 3 hari:
1. Klik tombol **"Analytics & Histori"** di sudut kanan atas navbar Dashboard utama, atau
2. Akses URL langsung di browser: [http://localhost:8000/analytics.html](http://localhost:8000/analytics.html)

Di halaman ini Anda dapat melihat:
- Total akumulasi seluruh hari
- Jam paling ramai kedatangan pengunjung
- Hari dengan jumlah pengunjung tertinggi
- Tabel breakdown per-hari (Total Masuk, Total Keluar, dan Puncak *Peak Inside*)
- Grafik perbandingan harian & pola jam kedatangan

---

### Langkah 4 (Opsional): Simulasi Pengunjung Tanpa Kamera

Jika Anda ingin menguji dashboard dan WebSocket tanpa menggunakan kamera fisik:

```bash
python sim_test.py
```
*Skrip ini akan secara otomatis mengirimkan data lalu lintas pengunjung acak ke API setiap 2 detik dan hasilnya langsung terlihat di Dashboard.*

---

### Langkah 5: Mereset Angka Hitungan Pengunjung

Untuk mengosongkan/mereset angka hitungan pengunjung dan data histori harian:

- **Lewat Skrip Python**:
  ```bash
  python reset_db.py
  ```
- **Lewat Dashboard UI**: Klik tombol **Reset Hitungan** di sudut kanan atas navigasi Dashboard dan konfirmasi dialog prompt.
- **Lewat API (cURL / HTTP client)**:
  ```bash
  curl -X POST http://localhost:8000/api/events/1/reset
  ```

---

## Pengaturan Multi-PC / Jaringan Terpisah

Jika Anda ingin menjalankan **Backend Server** di satu PC (misalnya PC Server di IP `192.168.1.100`) dan **Kamera Runner** di PC lain:

1. **Di PC Server**: Jalankan FastAPI Uvicorn dengan host `0.0.0.0`:
   ```bash
   uvicorn src.api.app:app --host 0.0.0.0 --port 8000
   ```
2. **Di PC Kamera Node**: Jalankan `camera_runner.py` dengan mengarahkan parameter `--api-url`:
   ```bash
   python camera_runner.py --camera-id 1 --source 0 --api-url "http://192.168.1.100:8000/api/count"
   ```

---

## Pengujian (Testing)

Untuk memastikan seluruh modul backend, database, service aggregator, endpoint API analytics, dan asset frontend berjalan normal:

```bash
pytest
```

---

## Struktur Proyek

```text
visitor-counter/
├── camera_runner.py      # Skrip utama pendeteksi AI & runner kamera real-time
├── sim_test.py           # Skrip simulasi lalu lintas pengunjung (tanpa kamera)
├── reset_db.py           # Skrip pengosongan/reset database counter
├── requirements.txt      # Daftar dependensi Python
├── yolov8n.pt            # Pretrained Model YOLOv8 Body Detection
├── visitor_counter.db    # Database SQLite (dibuat otomatis)
├── DESIGN.md             # Panduan UI/UX & Design System
├── PRODUCT.md            # Dokumentasi Spesifikasi Produk & MVP Scope
├── docs/                 # Dokumentasi internal, rencana fase & spesifikasi desain
├── src/
│   ├── api/              # Endpoint FastAPI (REST & WebSockets, /analytics)
│   ├── db/               # Inisialisasi Database SQLite & Model SQLAlchemy (DailyRecord, WIB)
│   ├── engine/           # Logika AI Tracking & Line Crossing Counter (YOLOv8)
│   ├── services/         # Service Agregasi Hitungan Pengunjung & Analytics Harian
│   └── static/           # Asset Frontend (HTML, CSS, JS Dashboard & Analytics Page)
└── tests/                # Unit test & Integration test (Pytest)
```
