"""Halaman Pengaturan: threshold monitoring (FR-22)."""
import customtkinter as ctk

from data import database
from ui.tema import (BIRU, BIRU_GELAP, HIJAU, MERAH, TEKS, TEKS_PUDAR,
                     buat_font, buat_kartu, tombol_biru, tombol_garis)

# (nama di config, judul, keterangan, langkah slider, format tampilan)
PENGATURAN = [
    ("AMBANG_EAR", "Ambang EAR",
     "Di bawah angka ini mata dianggap tertutup", 0.01, "{:.2f}"),
    ("RASIO_TERLALU_DEKAT", "Rasio terlalu dekat",
     "Wajah sebesar ini dibanding patokan kalibrasi dianggap terlalu dekat", 0.05, "{:.2f}x"),
    ("DURASI_KUNCI_DETIK", "Durasi sebelum kunci layar",
     "Lama terlalu dekat sebelum layar Windows dikunci", 1, "{:.0f} dtk"),
    ("KEDIP_MIN_PER_MENIT", "Kedip minimum per menit",
     "Di bawah angka ini mata dianggap lelah", 1, "{:.0f} per menit"),
    ("DURASI_MENGANTUK", "Durasi mata tertutup",
     "Mata tertutup lebih lama dari ini dianggap mengantuk", 0.1, "{:.1f} dtk"),
]


class HalamanPengaturan(ctk.CTkScrollableFrame):
    def __init__(self, master, monitor):
        super().__init__(master, fg_color="transparent")
        self.monitor = monitor
        self.f_judul, self.f_besar, self.f_fatigue, self.f_tebal, self.f_kecil = buat_font()
        self.slider = {}
        self.nilai_label = {}
        self.format = {}
        self._induk = master
        self._toast = None
        self._toast_job = None
        self._buat()

    def _kartu(self):
        k = buat_kartu(self)
        k.pack(fill="x", padx=24, pady=8)
        return k

    def _buat(self):
        ctk.CTkLabel(self, text="Pengaturan", font=self.f_judul, text_color=TEKS
                     ).pack(anchor="w", padx=24, pady=(20, 0))
        ctk.CTkLabel(self, text="Perubahan langsung berlaku, tanpa perlu menjalankan ulang aplikasi.",
                     font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w", padx=24, pady=(0, 10))

        # --- threshold ---
        kartu = self._kartu()
        ctk.CTkLabel(kartu, text="Threshold monitoring", font=self.f_tebal, text_color=TEKS
                     ).pack(anchor="w", padx=18, pady=(14, 2))

        for nama, judul, ket, langkah, fmt in PENGATURAN:
            minimum, maksimum, _ = database.BATAS[nama]
            self.format[nama] = fmt
            baris = ctk.CTkFrame(kartu, fg_color="transparent")
            baris.pack(fill="x", padx=18, pady=8)
            atas = ctk.CTkFrame(baris, fg_color="transparent")
            atas.pack(fill="x")
            ctk.CTkLabel(atas, text=judul, font=self.f_tebal, text_color=TEKS).pack(side="left")
            nilai = ctk.CTkLabel(atas, text="", font=self.f_tebal, text_color=BIRU)
            nilai.pack(side="right")
            self.nilai_label[nama] = nilai
            ctk.CTkLabel(baris, text=ket, font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w")
            jumlah_langkah = max(1, round((maksimum - minimum) / langkah))
            s = ctk.CTkSlider(baris, from_=minimum, to=maksimum, number_of_steps=jumlah_langkah,
                              progress_color=BIRU, button_color=BIRU, button_hover_color=BIRU_GELAP,
                              command=lambda v, n=nama: self._geser(n, v))
            s.pack(fill="x", pady=(6, 0))
            self.slider[nama] = s

        tombol = ctk.CTkFrame(kartu, fg_color="transparent")
        tombol.pack(fill="x", padx=18, pady=(10, 4))
        tombol_biru(tombol, "Simpan", self._simpan).pack(side="left")
        tombol_garis(tombol, "Kembalikan default", self._reset).pack(side="left", padx=10)
        self.lbl_pesan = ctk.CTkLabel(kartu, text="", font=self.f_kecil, text_color=TEKS_PUDAR,
                                      anchor="w")
        self.lbl_pesan.pack(anchor="w", padx=18, pady=(4, 14))

        # --- kalibrasi ---
        k2 = self._kartu()
        ctk.CTkLabel(k2, text="Kalibrasi jarak", font=self.f_tebal, text_color=TEKS
                     ).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(k2, text="Duduk di jarak yang nyaman dan hadap layar, lalu tekan tombol di bawah.",
                     font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w", padx=18)
        tombol_biru(k2, "Kalibrasi ulang jarak", self._kalibrasi).pack(anchor="w", padx=18, pady=(10, 4))
        self.lbl_kal = ctk.CTkLabel(k2, text="", font=self.f_kecil, text_color=TEKS_PUDAR)
        self.lbl_kal.pack(anchor="w", padx=18, pady=(0, 14))

    # --- aksi ---
    def segarkan(self):
        """Dipanggil tiap halaman ini dibuka: tampilkan nilai yang sedang berlaku."""
        for nama, nilai in database.ambil_threshold().items():
            self.slider[nama].set(nilai)
            self._geser(nama, nilai)
        self.lbl_pesan.configure(text="")
        self.lbl_kal.configure(text="")

    def _geser(self, nama, nilai):
        self.nilai_label[nama].configure(text=self.format[nama].format(nilai))

    def _pesan(self, teks, warna):
        self.lbl_pesan.configure(text=teks, text_color=warna)
        self._toast_tampil(teks, warna)

    def _toast_tampil(self, teks, warna):
        """Pop-up kecil di atas halaman, hilang sendiri setelah 3 detik."""
        if self._toast is None:
            self._toast = ctk.CTkLabel(self._induk, text="", font=self.f_tebal,
                                       text_color="white", corner_radius=12, height=44)
        if self._toast_job is not None:
            self.after_cancel(self._toast_job)
        self._toast.configure(text=f"   {teks}   ", fg_color=warna)
        self._toast.place(relx=0.5, y=16, anchor="n")
        self._toast.lift()
        self._toast_job = self.after(3000, self._toast_sembunyi)

    def _toast_sembunyi(self):
        if self._toast is not None:
            self._toast.place_forget()
        self._toast_job = None

    def _simpan(self):
        nilai = {nama: round(float(s.get()), 2) for nama, s in self.slider.items()}
        try:
            ok, pesan = database.simpan_threshold(nilai)
        except Exception:
            self._pesan("Gagal menyimpan pengaturan. Coba lagi.", MERAH)
            return
        self._pesan(pesan, HIJAU if ok else MERAH)

    def _reset(self):
        try:
            database.reset_threshold()
        except Exception:
            self._pesan("Gagal mengembalikan pengaturan. Coba lagi.", MERAH)
            return
        self.segarkan()
        self._pesan("Pengaturan dikembalikan ke nilai awal.", HIJAU)

    def _kalibrasi(self):
        if self.monitor.ambil_data()["berjalan"]:
            self.monitor.kalibrasi()
            self.lbl_kal.configure(text="Kalibrasi diminta. Tetap duduk normal selama beberapa detik.",
                                   text_color=BIRU)
        else:
            self.lbl_kal.configure(text="Monitoring belum berjalan. Mulai monitoring dulu.",
                                   text_color=MERAH)