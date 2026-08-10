# Event Visitor Counter

Sistem penghitung pengunjung acara (*event visitor counter*) secara *real-time* berbasis **YOLOv8** (Computer Vision), **FastAPI** (Backend REST & WebSockets), dan **Vanilla JS/CSS** (Live Dashboard & Multi-Day Analytics).

Sistem ini dirancang untuk pemantauan pengunjung melalui multiple kamera entry (masuk) dan exit (keluar), baik di jaringan lokal (LAN) maupun terdistribusi di beberapa node PC/perangkat terpisah. Dilengkapi dengan dukungan **Event Multi-Hari (3-Day Event)**, **Auto-Reset Harian**, **Google OAuth Authentication**, serta **Halaman Laporan Analytics**.

---

## Daftar Isi

1. [Fitur Utama](#fitur-utama)
2. [Prasyarat Sistem](#prasyarat-sistem)
3. [Konfigurasi Environment (`.env`)](#konfigurasi-environment-env)
4. [Panduan Setup Development](#panduan-setup-development)
   - [1. Clone Repository & Setup Virtual Environment](#1-clone-repository--setup-virtual-environment)
   - [2. Instalasi Dependensi Python](#2-instalasi-dependensi-python)
   - [3. Menjalankan Backend Server & Dashboard](#3-menjalankan-backend-server--dashboard)
   - [4. Menjalankan Kamera AI (Camera Runner)](#4-menjalankan-kamera-ai-camera-runner)
   - [5. Simulasi Pengunjung (Tanpa Kamera Fisik)](#5-simulasi-pengunjung-tanpa-kamera-fisik)
   - [6. Pengujian Unit & Integrasi (Testing)](#6-pengujian-unit--integrasi-testing)
5. [Panduan Setup Deployment (Production)](#panduan-setup-deployment-production)
   - [Opsi A: Bare-Metal / Mini PC (Debian 12 / Linux & Systemd)](#opsi-a-bare-metal--mini-pc-debian-12--linux--systemd)
   - [Opsi B: Containerized (Docker & Docker Compose)](#opsi-b-containerized-docker--docker-compose)
   - [Opsi C: Deployment Node Kamera Terdistribusi (Multi-PC)](#opsi-c-deployment-node-kamera-terdistribusi-multi-pc)
6. [Struktur Proyek](#struktur-proyek)
7. [Manajemen Database & Reset Hitungan](#manajemen-database--reset-hitungan)
8. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Fitur Utama

- **Real-Time Live Dashboard**: Streaming data instan via WebSockets saat pengunjung melewati garis deteksi.
- **Deteksi & Tracking AI Presisi (YOLOv8)**: Algoritma Line Crossing Counter untuk menghitung objek manusia secara realtime.
- **Pencatatan Multi-Hari & Auto-Reset**: Counter harian otomatis berulang dari `0` setiap pergantian hari (WIB / GMT+7), sementara histori hari-hari sebelumnya tersimpan rapi di database SQLite.
- **Laporan Analytics & Histori (`analytics.html`)**: Metrics komprehensif mencakup Total Akumulasi, Jam Terramai, Hari Peak, Tabel Breakdown Harian, dan Grafik Distribusi (Chart.js).
- **Multi-Camera Support**: Pemetaan fleksibel peran kamera (*MASUK* vs *KELUAR*) pada node yang terhubung.
- **Keamanan & Autentikasi**: Proteksi Google OAuth 2.0 untuk Dashboard Admin & Opsi HTTP Header API Key untuk ingest node kamera.
- **Siap Deployment**: Mendukung Systemd Linux Service (headless Mini PC) dan Docker / Docker Compose containerization.

---

## Prasyarat Sistem

### Hardware
- **Server/Backend**: PC / Laptop / Mini PC (Intel/AMD x86_64 atau ARM64, RAM minimal 4 GB).
- **Kamera Node**: Webcam USB, IP Camera RTSP stream, atau file video `.mp4`.
- **Koneksi Jaringan**: LAN Ethernet / Wi-Fi lokal untuk sinkronisasi antar-node.

### Software
- **Sistem Operasi**: Linux (Debian 12 / Ubuntu 22.04+ direkomendasikan) atau Windows 10/11.
- **Python**: Versi 3.9 s/d 3.11.
- **Paket Sistem Linux (jika menggunakan Linux/Debian)**: `ffmpeg`, `libgl1`, `libglib2.0-0`, `build-essential`.
- **Docker & Docker Compose** *(Opsional, untuk opsi deployment kontainer)*.

---

## Konfigurasi Environment (`.env`)

Buat atau sesuaikan file `.env` pada root direktori proyek sebelum menjalankan aplikasi:

```env
# Google OAuth Configuration (Authentication Admin Dashboard)
GOOGLE_CLIENT_ID=820009123535-ejfu9eoefbc0hdmrtgc40a2ne1f3qeca.apps.googleusercontent.com
ALLOWED_EMAILS=admin@example.com,user@example.com
SESSION_SECRET_KEY=secret_random_visitor_counter_wondrx_2026_key

# API Key untuk Otorisasi Kamera Node Remote (Opsional, kosongkan jika dev lokal)
API_KEY=my-secret-event-key

# Database Connection (Default SQLite)
DATABASE_URL=sqlite:///./visitor_counter.db
```

---

## Panduan Setup Development

### 1. Clone Repository & Setup Virtual Environment

Buka terminal di komputer Anda dan jalankan:

```bash
git clone <URL-REPOSITORY-ANDA> visitor-counter
cd visitor-counter
```

Buat dan aktifkan Virtual Environment Python:

- **Linux / macOS**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Windows (PowerShell / CMD)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```

### 2. Instalasi Dependensi Python

Pastikan virtual environment telah aktif, lalu tingkatkan `pip` dan install dependensi:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Menjalankan Backend Server & Dashboard

Jalankan FastAPI server menggunakan Uvicorn dalam mode reload:

```bash
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

Setelah server berjalan, akses antarmuka melalui browser:
- **Live Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Halaman Analytics**: [http://localhost:8000/analytics.html](http://localhost:8000/analytics.html)
- **Dokumentasi OpenAPI (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Menjalankan Kamera AI (Camera Runner)

Buka jendela terminal **baru** (dengan virtual environment aktif) untuk menjalankan modul deteksi visual:

#### A. Mode Interaktif (Wizard Input)
```bash
python camera_runner.py
```
*Sistem akan memandu Anda memasukkan Camera ID, Source Kamera (Webcam/RTSP/Video), dan Server URL secara bertahap.*

#### B. Mode CLI Direct Arguments
```bash
# Kamera Masuk (Camera ID #1) menggunakan Webcam lokal (Device index 0)
python camera_runner.py --camera-id 1 --source 0

# Kamera Keluar (Camera ID #3) menggunakan IP Camera (RTSP Stream)
python camera_runner.py --camera-id 3 --source "rtsp://admin:password@192.168.1.50:554/stream"

# Kamera menggunakan File Video Demo
python camera_runner.py --camera-id 1 --source "video_sample.mp4"
```

#### C. Opsi Pengaturan Garis Deteksi (Line Crossing)
```bash
# Garis Vertikal di Tengah Layar
python camera_runner.py --camera-id 1 --line-orientation vertical --line-position 0.5

# Garis Koordinat Kustom (x1, y1, x2, y2)
python camera_runner.py --camera-id 1 --line-coords "100,200,500,200"

# Mode Headless (Tanpa Jendela UI OpenCV Display)
python camera_runner.py --camera-id 1 --source 0 --no-window
```

### 5. Simulasi Pengunjung (Tanpa Kamera Fisik)

Untuk melakukan pengujian data alur pengunjung tanpa membutuhkan input kamera:

```bash
python sim_test.py
```
*Skrip akan mensimulasikan pengiriman event pengunjung secara acak ke backend server setiap 2 detik.*

### 6. Pengujian Unit & Integrasi (Testing)

Jalankan suite pengujian menggunakan `pytest` untuk memastikan integritas logika bisnis, API, dan skema database:

```bash
pytest
```

---

## Panduan Setup Deployment (Production)

### Opsi A: Bare-Metal / Mini PC (Debian 12 / Linux & Systemd)

Opsi ini direkomendasikan untuk deployment langsung pada hardware Mini PC (misalnya Mini PC Debian 12 Bookworm) yang diletakkan di lokasi acara.

#### 1. Instalasi Paket Dependensi OS Debian/Ubuntu
Jalankan perintah berikut via terminal SSH:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl python3 python3-venv python3-pip libgl1 libglib2.0-0 ffmpeg build-essential
```

#### 2. Preparation Project & Virtualenv
```bash
cd /home/admin
git clone <URL-REPOSITORY-ANDA> visitor-counter
cd visitor-counter
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Setup Auto-Start Service (Systemd)
Buat file service di direktori systemd:

```bash
sudo nano /etc/systemd/system/visitor-counter.service
```

Isikan konfigurasi service berikut (sesuaikan path folder dan username `User`):

```ini
[Unit]
Description=Visitor Counter Uvicorn FastAPI Server
After=network.target

[Service]
User=admin
WorkingDirectory=/home/admin/visitor-counter
ExecStart=/home/admin/visitor-counter/venv/bin/uvicorn src.api.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PORT=8000

[Install]
WantedBy=multi-user.target
```

Aktifkan dan jalankan daemon systemd:

```bash
sudo systemctl daemon-reload
sudo systemctl enable visitor-counter
sudo systemctl start visitor-counter
```

Periksa status keberhasilan service:

```bash
sudo systemctl status visitor-counter
```

#### Perintah Ringkasan Operasional Service
| Perintah | Fungsi |
| :--- | :--- |
| `sudo systemctl status visitor-counter` | Memeriksa status operasional server |
| `sudo systemctl restart visitor-counter` | Memuat ulang (restart) server |
| `sudo systemctl stop visitor-counter` | Menghentikan server |
| `sudo journalctl -u visitor-counter -f` | Memantau log real-time server |

---

### Opsi B: Containerized (Docker & Docker Compose)

Deployment menggunakan Docker memastikan lingkungan aplikasi terisolasi dan konsisten.

#### 1. Menggunakan Docker Compose (Direkomendasikan)

Pastikan Docker Engine dan Docker Compose sudah terpasang, kemudian jalankan:

```bash
# Jalankan kontainer di background
docker-compose up -d --build
```

Memeriksa log dan status kontainer:

```bash
docker-compose logs -f
docker-compose ps
```

Menghentikan kontainer:

```bash
docker-compose down
```

#### 2. Menggunakan Direct Docker CLI
```bash
# Build Image
docker build -t visitor-counter-server .

# Run Container
docker run -d \
  --name visitor_counter \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e API_KEY="my-secret-event-key" \
  visitor-counter-server
```

---

### Opsi C: Deployment Node Kamera Terdistribusi (Multi-PC)

Jika **Backend Server** di-deploy di Cloud VPS / PC Server Pusat (`192.168.1.100`) dan **Camera Runner** dijalankan pada PC Node terpisah di lokasi entry/exit:

1. **Pada Server Pusat (Cloud / Main PC)**:
   - Atur `API_KEY` pada file `.env` atau environment variable server.
   - Pastikan port `8000` terbuka dan dapat diakses dari jaringan kamera node.

2. **Pada PC Node Kamera**:
   - Install dependensi Python & OpenCV pada PC Node.
   - Jalankan `camera_runner.py` dengan mengarahkan URL API ke Server Pusat dan menyertakan `API_KEY`:

```bash
python camera_runner.py \
  --camera-id 1 \
  --source 0 \
  --api-url "http://192.168.1.100:8000/api/count" \
  --api-key "my-secret-event-key"
```

---

## Struktur Proyek

```text
visitor-counter/
├── camera_runner.py      # Module utama AI Tracking (YOLOv8) & runner kamera
├── sim_test.py           # Skrip simulasi pengiriman data lalu lintas pengunjung
├── reset_db.py           # Utility skrip untuk reset database counter
├── requirements.txt      # Manifest dependensi Python
├── Dockerfile            # Konfigurasi Docker Image Production
├── docker-compose.yml    # Orchestration Docker Compose
├── DESIGN.md             # Document Pedoman UI/UX & Design System
├── PRODUCT.md            # Document Spesifikasi Produk & MVP Scope
├── docs/                 # Dokumentasi internal & rancangan spesifikasi
├── src/
│   ├── api/              # Module FastAPI (REST Endpoints, WebSockets, Auth, Analytics)
│   ├── db/               # Inisialisasi Database SQLite & Schema Model SQLAlchemy
│   ├── engine/           # Logika Core AI Tracking & Line Crossing Counter
│   ├── services/         # Business logic agregasi data & laporan harian
│   └── static/           # Asset Frontend (HTML, CSS, JS Dashboard & Analytics Page)
└── tests/                # Automated Test Suite (Pytest)
```

---

## Manajemen Database & Reset Hitungan

Secara default, aplikasi menyimpan data akumulasi dan log harian pada database SQLite `visitor_counter.db` (atau `/app/data/visitor_counter.db` pada mode Docker).

Untuk mereset seluruh angka hitungan dan histori data:
- **Melalui Script Terminal**:
  ```bash
  python reset_db.py
  ```
- **Melalui Dashboard Interface**: Klik tombol **Reset Hitungan** pada navigasi atas Live Dashboard.
- **Melalui REST API**:
  ```bash
  curl -X POST http://localhost:8000/api/events/1/reset
  ```

---

## Troubleshooting & FAQ

### 1. `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` (OpenCV Display Error di Server Headless)
Saat menjalankan `camera_runner.py` di server Linux tanpa layar GUI/Desktop:
- Gunakan flag `--no-window`:
  ```bash
  python camera_runner.py --camera-id 1 --source 0 --no-window
  ```

### 2. Port `8000` sudah digunakan (*Address already in use*)
- Periksa proses yang menggunakan port `8000`:
  ```bash
  sudo lsof -i :8000
  ```
- Hentikan proses tersebut atau jalankan Uvicorn di port lain:
  ```bash
  uvicorn src.api.app:app --port 8080
  ```

### 3. Google OAuth Login Gagal (*403 Forbidden* atau *Invalid Token*)
- Pastikan `GOOGLE_CLIENT_ID` di file `.env` telah sesuai dengan konfigurasi Google Cloud Console.
- Pastikan email login Anda tercantum pada `ALLOWED_EMAILS` di `.env`.
