# Design Spec: ONNX and ByteTrack Integration

Menyediakan opsi penggunaan model ONNX (`.onnx`) di samping model PyTorch (`.pt`) asli, serta algoritma pelacakan ByteTrack untuk meningkatkan FPS dan kehalusan deteksi pada hardware CPU (Intel/AMD) maupun Integrated GPU.

## Masalah & Kebutuhan
* **Masalah:** Model deteksi `yolov8n.pt` (Nano PyTorch) pada CPU sering menghasilkan kotak deteksi bergetar (*jittery*) dan kehilangan objek, sehingga akurasi perhitungan orang lewat berkurang. Di sisi lain, menaikkan ke model Small/Medium PyTorch di CPU membuat FPS turun secara drastis (di bawah 15 FPS).
* **Kebutuhan:** 
  1. Kecepatan pemrosesan yang lebih tinggi (mencapai 20-30 FPS) untuk kehalusan pelacakan (*tracking*).
  2. Fleksibilitas menjalankan aplikasi di CPU Intel (Iris Xe) maupun AMD Ryzen (Radeon iGPU).
  3. Kemudahan memilih antara performa tinggi (ONNX) atau kompatibilitas standar (PyTorch) secara dinamis.

## Solusi yang Diusulkan
1. **Dukungan Format ONNX:** Ekspor model YOLOv8 ke format ONNX (`.onnx`) dan jalankan melalui `onnxruntime` untuk optimasi CPU universal.
2. **Pilihan Tracker ByteTrack:** Menggunakan tracker ByteTrack yang lebih ringan daripada BoT-SORT untuk menghemat beban CPU.
3. **Argumen CLI & Interaktif Fleksibel:** Menambahkan opsi `--model-name` dan `--tracker` pada runner kamera sehingga pengguna bisa berpindah format dan tracker dengan mudah.

---

## Perubahan Komponen

### 1. Dependensi (`requirements.txt`)
Menambahkan `onnx` dan `onnxruntime` untuk mendukung eksekusi model ONNX pada CPU.

### 2. Skrip Ekspor Model (`export_model.py`)
Skrip baru untuk mengotomatiskan konversi model dari `.pt` ke `.onnx` dengan resolusi input default 640x640.

### 3. Runner Kamera (`camera_runner.py`)
* Menambahkan parser argumen `--model-name` (default: `yolov8s.onnx`) dan `--tracker` (default: `bytetrack.yaml`).
* Menambahkan pilihan ini pada menu interaktif (tanya-jawab saat dijalankan tanpa argumen).
* Meneruskan argumen tersebut ke kelas `CameraStreamProcessor`.

### 4. Pemroses Aliran Kamera (`src/engine/stream_processor.py`)
* Menyesuaikan constructor `__init__` untuk menerima `model_name` dan `tracker`.
* Memperbarui pemanggilan tracking `self.model.track(...)` dengan opsi `tracker=self.tracker`.

---

## Rencana Verifikasi

### Pengujian Otomatis
* Menjalankan unit test yang ada (`tests/`) untuk memastikan perubahan argumen tidak merusak fungsionalitas dasar database dan API.
* Membuat pengujian baru untuk inisialisasi `CameraStreamProcessor` dengan konfigurasi model ONNX dan tracker kustom.

### Pengujian Manual
1. Menjalankan perintah ekspor: `python export_model.py --model yolov8s.pt` untuk memastikan file `yolov8s.onnx` berhasil dibuat.
2. Menjalankan program menggunakan ONNX:
   ```bash
   python camera_runner.py --camera-id 1 --source "video_sample.mp4" --model-name yolov8s.onnx --tracker bytetrack.yaml
   ```
3. Menjalankan program menggunakan PyTorch biasa (kontrol komparasi):
   ```bash
   python camera_runner.py --camera-id 1 --source "video_sample.mp4" --model-name yolov8n.pt --tracker botsort.yaml
   ```
4. Membandingkan kelancaran visual (FPS) dan kestabilan pelacakan orang lewat di layar.
