# EyeGuard

Aplikasi untuk memantau kondisi mata dan jarak pengguna ke layar
menggunakan webcam. EyeGuard berjalan di latar belakang dan memberi peringatan
serta mengunci layar saat pengguna, misalnya anak yang sedang bermain,
duduk terlalu dekat dengan layar.

# Video Presentasi
[![Video presentasi EyeGuard](https://img.youtube.com/vi/mNdickXQzMc/hqdefault.jpg)](https://www.youtube.com/watch?v=mNdickXQzMc)

[Tonton video presentasi EyeGuard di YouTube](https://www.youtube.com/watch?v=mNdickXQzMc)

> Indikator kelelahan mata, bukan alat diagnosis medis.

## Fitur yang sudah berfungsi

- Deteksi wajah dan titik landmark mata (MediaPipe Face Mesh)
- Status mata terbuka atau tertutup dan penghitung kedip (Eye Aspect Ratio)
- Estimasi jarak wajah ke layar dengan kalibrasi
- Pop-up peringatan saat terlalu dekat
- Timer dan kunci layar otomatis Windows
- Indikator fatigue berbasis aturan: Normal, Lelah, Mengantuk
- Dashboard (customtkinter) dengan navbar, kartu status, kamera langsung, dan grafik kedip
- Berjalan di latar belakang lewat system tray
- Riwayat sesi dan statistik (SQLite)
- Pengaturan threshold yang tersimpan

## Teknologi

Python 3.11, OpenCV, MediaPipe, customtkinter, pystray, SQLite.

## Cara menjalankan

1. Pasang Python 3.11 (MediaPipe belum cocok dengan Python yang lebih baru).
2. Buka terminal di folder proyek, lalu buat dan aktifkan virtual environment:

   ```
   py -3.11 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Pasang library:

   ```
   python -m pip install -r requirements.txt
   ```

4. Jalankan:

   ```
   python main.py
   ```

## Cara memakai

1. Monitoring langsung jalan saat aplikasi dibuka.
2. Duduk di jarak yang nyaman, lalu tekan **Kalibrasi jarak**.
3. Nyalakan switch **Kunci layar otomatis**. Kalau wajah terlalu dekat melewati batas waktu, layar Windows dikunci.
4. Tombol X hanya menyembunyikan jendela. Monitoring tetap jalan di tray. Pilih **Keluar** di menu tray untuk menutup total.
5. Atur batas-batasnya di halaman **Pengaturan**, lihat sesi sebelumnya di halaman **Riwayat**.

## Struktur folder

```
main.py       
config.py     
core/             
data/           
ui/               
tests/        
docs/              
```

## Catatan

- Video webcam diproses langsung dan tidak disimpan. Yang disimpan hanya angka ringkasan sesi.
- Hasil deteksi dipengaruhi pencahayaan, posisi wajah, dan kualitas kamera.
