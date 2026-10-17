"""Halaman Riwayat: statistik, grafik, dan tabel sesi monitoring."""
import tkinter as tk

import customtkinter as ctk

import config
from data import database
from ui.tema import (BIRU, BIRU_MUDA, GARIS, MERAH, NAMA_FATIGUE, TEKS, TEKS_PUDAR,
                     WARNA_FATIGUE, buat_font, buat_kartu, format_durasi, format_waktu)

LEBAR_GRAFIK, TINGGI_GRAFIK = 640, 180

# (judul kolom, bobot lebar)
KOLOM = [("Waktu mulai", 3), ("Durasi", 2), ("Kedip/menit", 2),
         ("Terlalu dekat", 2), ("Fatigue", 2), ("", 1)]


class HalamanRiwayat(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.f_judul, self.f_besar, self.f_fatigue, self.f_tebal, self.f_kecil = buat_font()
        self.stat = {}
        self._buat()

    def _buat(self):
        ctk.CTkLabel(self, text="Riwayat Monitoring", font=self.f_judul,
                     text_color=TEKS).pack(anchor="w", padx=24, pady=(20, 0))
        ctk.CTkLabel(self, text="Ringkasan semua sesi monitoring yang tersimpan di komputer ini.",
                     font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w", padx=24, pady=(0, 10))

        # --- 4 kartu statistik ---
        baris = ctk.CTkFrame(self, fg_color="transparent")
        baris.pack(fill="x", padx=18, pady=6)
        daftar = [("sesi", "Total sesi"), ("waktu", "Total waktu"),
                  ("kedip", "Rata-rata kedip per menit"), ("dekat", "Kali terlalu dekat")]
        for i, (kunci, judul) in enumerate(daftar):
            baris.grid_columnconfigure(i, weight=1, uniform="stat")
            k = buat_kartu(baris)
            k.grid(row=0, column=i, padx=6, sticky="nsew")
            ctk.CTkLabel(k, text=judul, font=self.f_kecil, text_color=TEKS_PUDAR
                         ).pack(anchor="w", padx=18, pady=(14, 0))
            nilai = ctk.CTkLabel(k, text="-", font=self.f_besar, text_color=TEKS)
            nilai.pack(anchor="w", padx=18, pady=(0, 14))
            self.stat[kunci] = nilai

        # --- grafik ---
        g = buat_kartu(self)
        g.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(g, text="Kedip per menit tiap sesi", font=self.f_tebal, text_color=TEKS
                     ).pack(anchor="w", padx=18, pady=(14, 0))
        ctk.CTkLabel(g, text="10 sesi terakhir, garis putus = batas minimum",
                     font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w", padx=18, pady=(0, 8))
        self.canvas = tk.Canvas(g, width=LEBAR_GRAFIK, height=TINGGI_GRAFIK,
                                bg="white", highlightthickness=0)
        self.canvas.pack(anchor="w", padx=18, pady=(0, 14))

        # --- tabel sesi ---
        t = buat_kartu(self)
        t.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(t, text="Sesi terakhir", font=self.f_tebal, text_color=TEKS
                     ).pack(anchor="w", padx=18, pady=(14, 6))
        self.tabel = ctk.CTkFrame(t, fg_color="transparent")
        self.tabel.pack(fill="x", padx=18, pady=(0, 14))

        # --- detail peringatan ---
        d = buat_kartu(self)
        d.pack(fill="x", padx=24, pady=8)
        self.lbl_detail_judul = ctk.CTkLabel(d, text="Peringatan sesi", font=self.f_tebal,
                                             text_color=TEKS)
        self.lbl_detail_judul.pack(anchor="w", padx=18, pady=(14, 6))
        self.lbl_detail = ctk.CTkLabel(d, text="", font=self.f_kecil, text_color=TEKS,
                                       justify="left", anchor="w", wraplength=760)
        self.lbl_detail.pack(anchor="w", padx=18, pady=(0, 14))

        ctk.CTkLabel(self, text="EyeGuard · indikator kelelahan mata, bukan diagnosis medis",
                     font=self.f_kecil, text_color=TEKS_PUDAR).pack(pady=(8, 16))

    # --- isi data ---
    def segarkan(self):
        """Dipanggil tiap halaman ini dibuka."""
        try:
            total = database.ringkasan_total()
            riwayat = database.ambil_riwayat(20)
        except Exception:
            self._tampil_error()
            return

        self.stat["sesi"].configure(text=str(total["jumlah_sesi"]))
        self.stat["waktu"].configure(text=format_durasi(total["total_durasi"]))
        self.stat["kedip"].configure(text=f"{total['rata_kedip']:.0f}")
        self.stat["dekat"].configure(text=str(total["total_dekat"]))
        self._gambar_grafik(riwayat[:10][::-1])   # urut dari yang paling lama
        self._isi_tabel(riwayat)
        self._tampil_detail(None)

    def _tampil_error(self):
        for lbl in self.stat.values():
            lbl.configure(text="-")
        self.canvas.delete("all")
        for w in self.tabel.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.tabel, text="Data riwayat tidak dapat dimuat. Coba buka halaman ini lagi.",
                     font=self.f_kecil, text_color=MERAH).pack(anchor="w", pady=8)

    def _isi_tabel(self, riwayat):
        for w in self.tabel.winfo_children():
            w.destroy()
        for i, (_, bobot) in enumerate(KOLOM):
            self.tabel.grid_columnconfigure(i, weight=bobot, uniform="kol")
        for i, (judul, _) in enumerate(KOLOM):
            ctk.CTkLabel(self.tabel, text=judul, font=self.f_kecil, text_color=TEKS_PUDAR,
                         anchor="w").grid(row=0, column=i, sticky="w", pady=(0, 6))

        if not riwayat:
            ctk.CTkLabel(self.tabel, text="Belum ada riwayat. Mulai monitoring pertamamu.",
                         font=self.f_kecil, text_color=TEKS_PUDAR
                         ).grid(row=1, column=0, columnspan=len(KOLOM), sticky="w", pady=10)
            return

        for n, s in enumerate(riwayat, start=1):
            status = s["status_fatigue"] or "-"
            sel = [format_waktu(s["waktu_mulai"]), format_durasi(s["durasi_detik"]),
                   f"{s['kedip_per_menit']:.0f}", str(s["kali_terlalu_dekat"]),
                   NAMA_FATIGUE.get(status, status)]
            for i, teks in enumerate(sel):
                warna = WARNA_FATIGUE.get(status, TEKS) if i == 4 else TEKS
                ctk.CTkLabel(self.tabel, text=teks, font=self.f_kecil, text_color=warna,
                             anchor="w").grid(row=n, column=i, sticky="w", pady=4)
            ctk.CTkButton(self.tabel, text="Lihat", width=56, height=28, corner_radius=8,
                          fg_color=BIRU_MUDA, text_color=BIRU, hover_color="#D3E2FF",
                          command=lambda x=s: self._tampil_detail(x)
                          ).grid(row=n, column=5, sticky="e", pady=4)

    def _tampil_detail(self, sesi):
        if sesi is None:
            self.lbl_detail_judul.configure(text="Peringatan sesi")
            self.lbl_detail.configure(text="Klik tombol Lihat pada salah satu sesi di atas.")
            return
        try:
            daftar = database.ambil_peringatan(sesi["id"])
        except Exception:
            self.lbl_detail.configure(text="Peringatan sesi ini tidak dapat dimuat.")
            return
        teks = "\n".join(f"{p['waktu']}   {p['pesan']}" for p in daftar)
        self.lbl_detail_judul.configure(text=f"Peringatan sesi {format_waktu(sesi['waktu_mulai'])}")
        self.lbl_detail.configure(text=teks or "Tidak ada peringatan pada sesi ini.")

    def _gambar_grafik(self, sesi):
        c = self.canvas
        c.delete("all")
        w, h = LEBAR_GRAFIK, TINGGI_GRAFIK
        if not sesi:
            c.create_text(w / 2, h / 2, text="Belum ada data untuk ditampilkan",
                          fill=TEKS_PUDAR, font=("Segoe UI", 11))
            return

        kiri, bawah, atas = 10, 26, 18
        nilai = [s["kedip_per_menit"] for s in sesi]
        puncak = max(20, max(nilai) * 1.15)
        tinggi_area = h - bawah - atas

        def y(v):
            return h - bawah - (v / puncak) * tinggi_area

        c.create_line(kiri, h - bawah, w, h - bawah, fill=GARIS)
        batas = y(config.KEDIP_MIN_PER_MENIT)
        c.create_line(kiri, batas, w, batas, fill=MERAH, dash=(5, 4))

        langkah = (w - kiri) / len(sesi)
        lebar_bar = min(46, langkah * 0.6)
        for i, s in enumerate(sesi):
            tengah = kiri + langkah * (i + 0.5)
            v = s["kedip_per_menit"]
            c.create_rectangle(tengah - lebar_bar / 2, y(v), tengah + lebar_bar / 2,
                               h - bawah, fill=BIRU, outline="")
            c.create_text(tengah, y(v) - 9, text=f"{v:.0f}", fill=TEKS,
                          font=("Segoe UI", 10, "bold"))
            c.create_text(tengah, h - bawah + 12, text=format_waktu(s["waktu_mulai"])[:5],
                          fill=TEKS_PUDAR, font=("Segoe UI", 9))