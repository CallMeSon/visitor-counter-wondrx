# Product Requirements: Event Visitor Counter

## 1. Ringkasan Produk

Sistem penghitung pengunjung untuk event sekali jalan (konser, seminar, bazar), menggunakan 7 kamera AI (2 titik masuk, 5 titik keluar) untuk menghitung jumlah pengunjung secara real time dan menyimpan histori untuk dilihat setelah event selesai.

Dikerjakan solo dengan target MVP (Minimum Viable Product) siap pakai dalam waktu kurang dari 1 bulan.

## 2. Target Pengguna

**Panitia/organizer event.** Bukan developer, jadi dashboard harus mudah dibaca sekilas: angka besar, grafik sederhana, tanpa perlu training khusus untuk memakainya.

## 3. Konteks Penggunaan

- Event bersifat sekali jalan, bukan operasional harian venue permanen.
- Lokasi kamera bisa satu venue dengan LAN yang sama, atau tersebar di beberapa titik terpisah, tergantung event. Sistem perlu fleksibel menangani kedua skenario.
- Kamera dibeli/disewa khusus untuk kebutuhan ini, bukan memanfaatkan CCTV existing. Artinya spesifikasi kamera bisa disesuaikan dengan kebutuhan sistem (resolusi, sudut pandang, output RTSP) sejak awal.

## 4. Scope Fitur MVP

Mengingat target waktu di bawah 1 bulan dan dikerjakan solo, scope MVP dibuat seketat mungkin. Fitur di luar daftar ini masuk kategori "nice to have", bukan blocker untuk event pertama.

### 4.1 Harus Ada (Must Have)

- **Live counter**: jumlah pengunjung yang sedang berada di area event (total masuk dikurangi total keluar), update real time atau near real time.
- **Grafik tren sederhana**: menunjukkan naik turun jumlah pengunjung dari waktu ke waktu selama event berlangsung.
- **Histori per event**: data pengunjung tersimpan di database dan bisa dilihat kembali setelah event selesai, langsung dari dashboard. Tidak perlu fitur export.
- **Deteksi dan counting dari 7 kamera**: 2 kamera role entry, 5 kamera role exit, sesuai rancangan skema `camera_role` yang sudah dibahas sebelumnya.

### 4.2 Tidak Perlu di MVP (Out of Scope)

- Alert atau notifikasi kapasitas penuh. Confirmed tidak dibutuhkan sekarang, bisa jadi fitur lanjutan kalau nanti diperlukan.
- Export laporan ke PDF/Excel. Cukup dilihat di dashboard.
- Multi-tenant atau multi-event dashboard yang kompleks (kalau nanti sistem dipakai untuk banyak event berbeda, ini bisa jadi fase 2).
- Fitur manajemen user/role granular, karena pengguna hanya panitia, tidak perlu sistem permission berlapis.

## 5. Kebutuhan Non-Fungsional

- **Fleksibilitas jaringan**: karena lokasi kamera belum pasti (LAN lokal atau tersebar), desain backend perlu mendukung koneksi dari luar LAN sejak awal, misalnya lewat VPN atau API yang exposed dengan aman lewat internet. Ini jadi keputusan arsitektur penting yang perlu difinalisasi di awal, bukan ditambahkan belakangan.
- **Kesederhanaan setup**: karena dikerjakan solo dengan waktu terbatas, prioritaskan tools dan library yang cepat diimplementasi dibanding yang paling optimal secara performa. Contoh: pakai model deteksi pretrained (YOLOv8) tanpa training ulang, kecuali akurasi awal terbukti tidak memadai.
- **Reliabilitas dasar**: kalau koneksi kamera ke backend putus sesaat, data tidak boleh hilang total. Minimal ada retry mechanism sederhana di sisi core layer.

## 6. Batasan dan Asumsi

- Belum ada kepastian apakah event pertama berlokasi di satu venue atau tersebar, sehingga desain jaringan harus mengasumsikan skenario terburuk (tersebar) supaya tidak perlu rombak arsitektur di tengah jalan.
- Tidak ada anggaran atau timeline untuk training model AI custom. Sistem mengandalkan model pretrained yang sudah terbukti akurat untuk deteksi orang secara umum.
- Solo developer berarti scope harus realistis. Kalau dalam perjalanan ternyata 1 bulan tidak cukup untuk semua fitur must-have, prioritas berikutnya adalah mengorbankan kualitas UI dashboard dulu, bukan mengorbankan akurasi counting.

## 7. Pertanyaan Terbuka (Belum Terjawab)

Hal-hal berikut masih perlu diputuskan sebelum masuk tahap development, karena berpengaruh langsung ke keputusan arsitektur:

- Kapan dan di mana event pertama akan berlangsung, supaya bisa dipastikan apakah butuh setup VPN atau cukup LAN lokal.
- Berapa kapasitas maksimal venue yang biasa dipakai, untuk memastikan performa live counter tidak masalah di angka pengunjung tertinggi.
- Apakah panitia akan mengakses dashboard dari HP atau laptop, ini menentukan prioritas desain responsif dashboard.

## 8. Definisi Selesai (Definition of Done) untuk MVP

MVP dianggap siap dipakai kalau:

1. Live counter menampilkan angka yang akurat dibandingkan hitungan manual pada uji coba terbatas.
2. Grafik tren tampil dan ter-update selama simulasi event berjalan.
3. Data histori tersimpan dan bisa diakses kembali setelah simulasi selesai.
4. Sistem tetap berjalan (tidak crash) saat diuji minimal 2-3 jam berturut-turut, mensimulasikan durasi event nyata.