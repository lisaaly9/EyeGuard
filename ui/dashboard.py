import queue
import time
import tkinter as tk
from collections import deque
import customtkinter as ctk
import cv2
from PIL import Image
import config
from data import database
from ui.panel_login import PanelLogin
from ui.halaman_pengaturan import HalamanPengaturan
from ui.halaman_riwayat import HalamanRiwayat
from ui.popup import PopupPeringatan
from ui.tema import (AMBER, BIRU, BIRU_MUDA, GARIS, HIJAU, KET_FATIGUE, LATAR, MERAH, NAMA_FATIGUE, PESAN_FATIGUE, TEKS, TEKS_PUDAR, WARNA_FATIGUE, buat_font, buat_kartu, tombol_biru, tombol_garis)
from ui.tray import Tray

ctk.set_appearance_mode("light")

LEBAR_KAMERA, TINGGI_KAMERA = 360, 270
LEBAR_GRAFIK, TINGGI_GRAFIK = 300, 110
HALAMAN = ["Beranda", "Dashboard", "Riwayat", "Premium", "Pengaturan"]


class Dashboard(ctk.CTk):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        self.pengguna = None
        self.title("EyeGuard")
        self.geometry("1180x820")
        self.minsize(1000, 700)
        self.configure(fg_color=LATAR)

        self.f_judul, self.f_besar, self.f_fatigue, self.f_tebal, self.f_kecil = buat_font()

        self.riwayat_kedip = deque(maxlen=60)   # sampel kedip/menit, 1 per detik
        self._sampel_terakhir = 0.0
        self._pesan_sampai = 0.0
        self._progres_terakhir = None
        self._kamera_hidup = False
        self._job = None
        self.tombol_nav = {}
        self.halaman = {}
        self.antrian = queue.Queue()
        self.popup = PopupPeringatan(self)
        self._kosong = ctk.CTkImage(
            light_image=Image.new("RGB", (LEBAR_KAMERA, TINGGI_KAMERA), "#0B1B3F"),
            size=(LEBAR_KAMERA, TINGGI_KAMERA),
        )

        self._buat_navbar()
        self.isi = ctk.CTkFrame(self, fg_color="transparent")
        self.isi.pack(fill="both", expand=True)
        self._buat_dashboard()
        self._buat_halaman_lain()
        self.buka_halaman("Beranda")

        self.protocol("WM_DELETE_WINDOW", self.sembunyikan)
        self.tray = Tray(self.antrian.put)
        self.tray.mulai()
        self.panel_login = PanelLogin(self)
        self._segarkan()

    def _buat_navbar(self):
        bar = ctk.CTkFrame(self, fg_color="white", corner_radius=0, height=64)
        bar.pack(fill="x")
        ctk.CTkLabel(bar, text="EyeGuard", text_color=TEKS, font=ctk.CTkFont(size=22, weight="bold")).pack(side="left", padx=(24, 28), pady=14)
        for nama in HALAMAN:
            tombol = ctk.CTkButton(bar, text=nama, width=96, height=36, corner_radius=18, fg_color="transparent", text_color=TEKS_PUDAR, hover_color=BIRU_MUDA, command=lambda n=nama: self.buka_halaman(n))
            tombol.pack(side="left", padx=2)
            self.tombol_nav[nama] = tombol
        self.btn_akun = ctk.CTkButton(bar, text="Masuk", width=80, height=32, corner_radius=16, fg_color="transparent", text_color=BIRU, hover_color=BIRU_MUDA, command=self._klik_akun)
        self.btn_akun.pack(side="right", padx=(0, 20))
        self.lbl_akun = ctk.CTkLabel(bar, text="", text_color=TEKS_PUDAR, font=self.f_kecil)
        self.lbl_akun.pack(side="right", padx=(0, 12))
        ctk.CTkFrame(self, fg_color=GARIS, corner_radius=0, height=1).pack(fill="x")

    def _kartu_status(self, parent, kolom, judul):
        k = buat_kartu(parent)
        k.grid(row=0, column=kolom, padx=6, sticky="nsew")
        ctk.CTkLabel(k, text=judul, font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w", padx=18, pady=(14, 0))
        nilai = ctk.CTkLabel(k, text="-", font=self.f_besar, text_color=TEKS)
        nilai.pack(anchor="w", padx=18)
        ket = ctk.CTkLabel(k, text="", font=self.f_kecil, text_color=TEKS_PUDAR)
        ket.pack(anchor="w", padx=18, pady=(0, 14))
        return nilai, ket

    def _buat_beranda(self):
        h = ctk.CTkScrollableFrame(self.isi, fg_color="transparent")
        self.halaman["Beranda"] = h

        ctk.CTkLabel(h, text="Selamat datang di EyeGuard", font=self.f_judul, text_color=TEKS).pack(anchor="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(h, text="Aplikasi pemantau kondisi mata dan jarak ke layar lewat webcam, "
                             "berjalan di latar belakang seperti VPN.",
                     font=self.f_kecil, text_color=TEKS_PUDAR, wraplength=700, justify="left").pack(anchor="w", padx=24, pady=(0, 16))

        tombol_biru(h, "Mulai monitoring sekarang", self._mulai_dari_beranda).pack(anchor="w", padx=24, pady=(0, 20))

        baris = ctk.CTkFrame(h, fg_color="transparent")
        baris.pack(fill="x", padx=18, pady=6)
        for i in range(4):
            baris.grid_columnconfigure(i, weight=1, uniform="beranda")
        self.rb_sesi = self._kartu_ringkasan(baris, 0, "Total sesi")
        self.rb_waktu = self._kartu_ringkasan(baris, 1, "Total waktu")
        self.rb_kedip = self._kartu_ringkasan(baris, 2, "Rata-rata kedip")
        self.rb_dekat = self._kartu_ringkasan(baris, 3, "Kali terlalu dekat")

        ctk.CTkLabel(h, text="Fitur utama", font=self.f_tebal, text_color=TEKS).pack(anchor="w", padx=24, pady=(24, 8))
        for teks in (
            "Deteksi wajah, mata, dan arah pandangan lewat webcam (MediaPipe)",
            "Estimasi jarak ke layar dengan kalibrasi otomatis",
            "Peringatan dan kunci layar otomatis saat terlalu dekat",
            "Indikator fatigue dari pola kedipan",
            "Riwayat dan statistik tiap sesi monitoring",
        ):
            ctk.CTkLabel(h, text=f"•  {teks}", font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w", padx=36, pady=2)
        ctk.CTkLabel(h, text="EyeGuard · indikator kelelahan mata, bukan diagnosis medis",font=self.f_kecil, text_color=TEKS_PUDAR).pack(pady=(24, 16))

    def _kartu_ringkasan(self, parent, kolom, judul):
        k = buat_kartu(parent)
        k.grid(row=0, column=kolom, padx=6, sticky="nsew")
        ctk.CTkLabel(k, text=judul, font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w", padx=18, pady=(14, 0))
        nilai = ctk.CTkLabel(k, text="-", font=self.f_besar, text_color=TEKS)
        nilai.pack(anchor="w", padx=18, pady=(0, 14))
        return nilai

    def segarkan_beranda(self):
        r = database.ringkasan_total()
        self.rb_sesi.configure(text=str(r["jumlah_sesi"]))
        self.rb_waktu.configure(text=f"{int(r['total_durasi'] // 60)} mnt")
        self.rb_kedip.configure(text=f"{r['rata_kedip']:.0f}/mnt")
        self.rb_dekat.configure(text=str(r["total_dekat"]))

    def _mulai_dari_beranda(self):
        self.buka_halaman("Dashboard")
        if not self.monitor.ambil_data()["berjalan"]:
            self._toggle_monitoring()

    def _buat_dashboard(self):
        h = ctk.CTkScrollableFrame(self.isi, fg_color="transparent")
        self.halaman["Dashboard"] = h

        # judul dan tombol
        atas = ctk.CTkFrame(h, fg_color="transparent")
        atas.pack(fill="x", padx=24, pady=(20, 10))
        kiri = ctk.CTkFrame(atas, fg_color="transparent")
        kiri.pack(side="left")
        ctk.CTkLabel(kiri, text="Dashboard Monitoring", font=self.f_judul,text_color=TEKS).pack(anchor="w")
        self.lbl_status = ctk.CTkLabel(kiri, text="", font=self.f_kecil, text_color=TEKS_PUDAR)
        self.lbl_status.pack(anchor="w")
        self.btn_toggle = tombol_biru(atas, "Mulai monitoring", self._toggle_monitoring)
        self.btn_toggle.pack(side="right")
        tombol_garis(atas, "Kalibrasi jarak", self._kalibrasi).pack(side="right", padx=10)

        # kartu status
        baris = ctk.CTkFrame(h, fg_color="transparent")
        baris.pack(fill="x", padx=18, pady=6)
        for i in range(4):
            baris.grid_columnconfigure(i, weight=1, uniform="kartu")
        self.k_mata, self.k_mata_ket = self._kartu_status(baris, 0, "Status mata")
        self.k_kedip, self.k_kedip_ket = self._kartu_status(baris, 1, "Kedipan")
        self.k_jarak, self.k_jarak_ket = self._kartu_status(baris, 2, "Jarak ke layar")
        self.k_fatigue, self.k_fatigue_ket = self._kartu_status(baris, 3, "Indikator fatigue")

        # kamera + fatigue
        tengah = ctk.CTkFrame(h, fg_color="transparent")
        tengah.pack(fill="x", padx=18, pady=6)
        tengah.grid_columnconfigure(0, weight=0)
        tengah.grid_columnconfigure(1, weight=1)

        kam = buat_kartu(tengah)
        kam.grid(row=0, column=0, padx=6, sticky="nsew")
        ctk.CTkLabel(kam, text="Pemantauan langsung", font=self.f_tebal, text_color=TEKS).pack(anchor="w", padx=18, pady=(14, 8))
        self.label_kamera = ctk.CTkLabel(kam, text="Monitoring belum berjalan", image=self._kosong, text_color="white", width=LEBAR_KAMERA, height=TINGGI_KAMERA, corner_radius=12)
        self.label_kamera.pack(padx=18, pady=(0, 18))

        fat = buat_kartu(tengah)
        fat.grid(row=0, column=1, padx=6, sticky="nsew")
        ctk.CTkLabel(fat, text="Indikator fatigue", font=self.f_tebal, text_color=TEKS).pack(anchor="w", padx=18, pady=(14, 0))
        self.lbl_fatigue = ctk.CTkLabel(fat, text="-", font=self.f_fatigue, text_color=TEKS)
        self.lbl_fatigue.pack(pady=(30, 6))
        self.lbl_pesan = ctk.CTkLabel(fat, text="", font=self.f_kecil, text_color=TEKS_PUDAR,wraplength=300, justify="center")
        self.lbl_pesan.pack(padx=18)
        ctk.CTkFrame(fat, fg_color=GARIS, height=1).pack(fill="x", padx=18, pady=(26, 12), side="bottom")
        baris_kunci = ctk.CTkFrame(fat, fg_color="transparent")
        baris_kunci.pack(fill="x", padx=18, pady=(0, 6), side="bottom")
        teks_kunci = ctk.CTkFrame(baris_kunci, fg_color="transparent")
        teks_kunci.pack(side="left")
        ctk.CTkLabel(teks_kunci, text="Kunci layar otomatis", font=self.f_tebal,text_color=TEKS).pack(anchor="w")
        ctk.CTkLabel(teks_kunci, text="Jika terlalu dekat melewati batas waktu",font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w")
        self.switch_kunci = ctk.CTkSwitch(baris_kunci, text="", width=46, progress_color=BIRU,command=self._ubah_kunci)
        self.switch_kunci.deselect()   # awalnya mati, sama dengan kondisi ScreenLocker
        self.switch_kunci.pack(side="right")

        # grafik, jarak, peringatan
        bawah = ctk.CTkFrame(h, fg_color="transparent")
        bawah.pack(fill="x", padx=18, pady=6)
        bawah.grid_columnconfigure(0, weight=3, uniform="b")
        bawah.grid_columnconfigure(1, weight=2, uniform="b")
        bawah.grid_columnconfigure(2, weight=3, uniform="b")

        g = buat_kartu(bawah)
        g.grid(row=0, column=0, padx=6, sticky="nsew")
        ctk.CTkLabel(g, text="Kedip per menit", font=self.f_tebal, text_color=TEKS).pack(anchor="w", padx=18, pady=(14, 0))
        ctk.CTkLabel(g, text="60 detik terakhir, garis putus = batas minimum",font=self.f_kecil, text_color=TEKS_PUDAR).pack(anchor="w", padx=18, pady=(0, 8))
        self.canvas = tk.Canvas(g, width=LEBAR_GRAFIK, height=TINGGI_GRAFIK,bg="white", highlightthickness=0)
        self.canvas.pack(padx=18, pady=(0, 14))
        self._gambar_grafik()

        j = buat_kartu(bawah)
        j.grid(row=0, column=1, padx=6, sticky="nsew")
        ctk.CTkLabel(j, text="Jarak ke layar", font=self.f_tebal, text_color=TEKS).pack(anchor="w", padx=18, pady=(14, 8))
        self.lbl_jarak = ctk.CTkLabel(j, text="-", font=self.f_besar, text_color=TEKS)
        self.lbl_jarak.pack()
        self.lbl_rasio = ctk.CTkLabel(j, text="", font=self.f_kecil, text_color=TEKS_PUDAR)
        self.lbl_rasio.pack(pady=(0, 10))
        self.progres_jarak = ctk.CTkProgressBar(j, width=190, height=10, fg_color=BIRU_MUDA,progress_color=BIRU)
        self.progres_jarak.set(0)
        self.progres_jarak.pack()
        self.lbl_sisa = ctk.CTkLabel(j, text="", font=self.f_kecil, text_color=AMBER)
        self.lbl_sisa.pack(pady=(10, 14))

        p = buat_kartu(bawah)
        p.grid(row=0, column=2, padx=6, sticky="nsew")
        ctk.CTkLabel(p, text="Peringatan terbaru", font=self.f_tebal, text_color=TEKS).pack(anchor="w", padx=18, pady=(14, 8))
        self.lbl_peringatan = ctk.CTkLabel(p, text="Belum ada peringatan.", font=self.f_kecil,text_color=TEKS, justify="left", anchor="w",wraplength=260)
        self.lbl_peringatan.pack(anchor="w", padx=18, pady=(0, 14))
        ctk.CTkLabel(h, text="EyeGuard · indikator kelelahan mata, bukan diagnosis medis",font=self.f_kecil, text_color=TEKS_PUDAR).pack(pady=(10, 16))

    def _buat_halaman_lain(self):
        self._buat_beranda()
        self.halaman["Riwayat"] = HalamanRiwayat(self.isi)
        self.halaman["Pengaturan"] = HalamanPengaturan(self.isi, self.monitor)
        f = ctk.CTkFrame(self.isi, fg_color="transparent")
        ctk.CTkLabel(f, text="Premium", font=self.f_judul, text_color=TEKS).pack(pady=(90, 8))
        ctk.CTkLabel(f, text="Halaman ini dikerjakan di tahap berikutnya.",
                     font=self.f_kecil, text_color=TEKS_PUDAR).pack()
        self.halaman["Premium"] = f

    def buka_halaman(self, nama):
        for f in self.halaman.values():
            f.pack_forget()
        self.halaman[nama].pack(fill="both", expand=True)
        if nama in ("Riwayat", "Pengaturan"):
            self.halaman[nama].segarkan()   # muat ulang data dari database
        elif nama == "Beranda":
            self.segarkan_beranda()
        for n, tombol in self.tombol_nav.items():
            if n == nama:
                tombol.configure(fg_color=BIRU, text_color="white", hover_color=BIRU)
            else:
                tombol.configure(fg_color="transparent", text_color=TEKS_PUDAR,hover_color=BIRU_MUDA)

    # akun
    def _klik_akun(self):
        if self.pengguna is None:
            self.panel_login.tampilkan()
        else:
            self._logout()

    def _butuh_login(self, lanjut):
        if self.pengguna is not None:
            lanjut()
        else:
            self.panel_login.tampilkan(setelah_masuk=lanjut)

    def _login_berhasil(self, pengguna, lanjut):
        self.pengguna = pengguna
        self._perbarui_navbar_akun()
        if lanjut is not None:
            lanjut()

    def _logout(self):
        self.pengguna = None
        self._perbarui_navbar_akun()
        self._tampil_pesan("Kamu sudah keluar.", TEKS_PUDAR)

    def _perbarui_navbar_akun(self):
        if self.pengguna is None:
            self.lbl_akun.configure(text="")
            self.btn_akun.configure(text="Masuk", text_color=BIRU)
        else:
            self.lbl_akun.configure(text=f"Halo, {self.pengguna['nama'].split()[0]}")
            self.btn_akun.configure(text="Keluar", text_color=MERAH)

    # aksi tombol
    def _toggle_monitoring(self):
        if self.monitor.ambil_data()["berjalan"]:
            self.monitor.berhenti()
            self.riwayat_kedip.clear()
            self._gambar_grafik()
            return
        self._butuh_login(self._mulai_monitoring_sekarang)

    def _mulai_monitoring_sekarang(self):
        if not self.monitor.mulai():
            self._tampil_pesan("Gagal memulai monitoring. Pastikan webcam tersedia.")

    def _kalibrasi(self):
        self._butuh_login(self._kalibrasi_sekarang)

    def _kalibrasi_sekarang(self):
        if self.monitor.ambil_data()["berjalan"]:
            self.monitor.kalibrasi()
            self._tampil_pesan("Kalibrasi jarak dimulai. Duduk normal dan hadap layar.", BIRU)
        else:
            self._tampil_pesan("Mulai monitoring dulu, baru kalibrasi jarak")

    def _ubah_kunci(self):
        aktif = bool(self.switch_kunci.get())
        if aktif != self.monitor.kunci.aktif:
            self.monitor.ubah_kunci()

    def _tampil_pesan(self, teks, warna=MERAH):
        self._pesan_sampai = time.time() + 4
        self._set(self.lbl_status, teks, warna)

    # jendela dan tray
    def sembunyikan(self):
        self.withdraw()
        self.tray.notifikasi("EyeGuard tetap berjalan di latar belakang.")

    def _tampilkan(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _tutup(self):
        if self._job is not None:
            self.after_cancel(self._job)
        self.popup.tutup()
        self.monitor.berhenti()
        self.tray.berhenti()
        self.destroy()

    def _proses_antrian(self):
        while not self.antrian.empty():
            perintah = self.antrian.get_nowait()
            if perintah == "buka":
                self._tampilkan()
            elif perintah == "toggle":
                self._toggle_monitoring()
            elif perintah == "keluar":
                self._tutup()
                return True
        return False

    # perbarui tampilan
    def _set(self, label, teks, warna=None):
        kunci = (teks, warna)
        if getattr(label, "_nilai_terakhir", None) == kunci:
            return
        label._nilai_terakhir = kunci
        if warna:
            label.configure(text=teks, text_color=warna)
        else:
            label.configure(text=teks)

    def _status_jarak(self, d, jalan, ada):
        if not jalan:
            return "-", TEKS, "Belum berjalan", 0
        if not ada:
            return "-", TEKS, "Wajah tidak terdeteksi", 0
        if not d["sudah_kalibrasi"]:
            return "Belum kalibrasi", AMBER, "Tekan Kalibrasi jarak", 0
        progres = min(d["rasio"] / 1.5, 1)
        ket = f"{d['rasio']:.2f}x · batas {config.RASIO_TERLALU_DEKAT:.2f}x"
        if d["terlalu_dekat"]:
            return "Terlalu dekat", MERAH, ket, progres
        return "Normal", HIJAU, ket, progres

    def _segarkan(self):
        if self._proses_antrian():
            return   # aplikasi sudah ditutup lewat menu tray

        d = self.monitor.ambil_data()
        jalan = d["berjalan"]
        ada = jalan and d["wajah"]
        tersembunyi = self.state() == "withdrawn"

        if not tersembunyi:
            self._segarkan_atas(d, jalan, ada)
            self._segarkan_kamera(jalan)
            self._segarkan_bawah(d, jalan, ada)

        self.popup.perbarui(d, ada)
        self._job = self.after(250 if tersembunyi else 40, self._segarkan)

    def _segarkan_atas(self, d, jalan, ada):
        # Status monitoring + tombol
        if time.time() >= self._pesan_sampai:
            if jalan:
                menit, detik = divmod(d["durasi"], 60)
                self._set(self.lbl_status, f"●  Monitoring aktif · berjalan {menit:02d}:{detik:02d}", HIJAU)
            else:
                self._set(self.lbl_status, "●  Monitoring belum berjalan", TEKS_PUDAR)
        teks_tombol = "Hentikan monitoring" if jalan else "Mulai monitoring"
        if self.btn_toggle.cget("text") != teks_tombol:
            self.btn_toggle.configure(text=teks_tombol)

        # Kartu mata
        if ada:
            tertutup = d["tertutup"]
            self._set(self.k_mata, "Tertutup" if tertutup else "Terbuka", MERAH if tertutup else HIJAU)
            self._set(self.k_mata_ket, f"EAR {d['ear']:.2f} · Pandangan: {d['arah_pandang']}")
        else:
            self._set(self.k_mata, "-", TEKS)
            self._set(self.k_mata_ket, "Wajah tidak terdeteksi" if jalan else "Belum berjalan")

        # Kartu kedip
        if jalan:
            self._set(self.k_kedip, f"{d['kedip_per_menit']:.0f}", TEKS)
            self._set(self.k_kedip_ket, f"per menit · total {d['kedip']}")
        else:
            self._set(self.k_kedip, "-", TEKS)
            self._set(self.k_kedip_ket, "Belum berjalan")

        # Kartu jarak
        judul, warna, ket, _ = self._status_jarak(d, jalan, ada)
        self._set(self.k_jarak, judul, warna)
        self._set(self.k_jarak_ket, ket)

        # Kartu fatigue
        if jalan:
            status = d["fatigue"]
            self._set(self.k_fatigue, NAMA_FATIGUE.get(status, status), WARNA_FATIGUE.get(status, TEKS_PUDAR))
            self._set(self.k_fatigue_ket, KET_FATIGUE.get(status, ""))
        else:
            self._set(self.k_fatigue, "-", TEKS)
            self._set(self.k_fatigue_ket, "Belum berjalan")

    def _segarkan_kamera(self, jalan):
        frame = self.monitor.ambil_frame() if jalan else None
        if frame is None:
            if self._kamera_hidup:
                self.label_kamera.configure(image=self._kosong, text="Monitoring belum berjalan")
                self._kamera_hidup = False
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gambar = Image.fromarray(rgb).resize((LEBAR_KAMERA, TINGGI_KAMERA))
        self._gambar = ctk.CTkImage(light_image=gambar, size=(LEBAR_KAMERA, TINGGI_KAMERA))
        self.label_kamera.configure(image=self._gambar, text="")
        self._kamera_hidup = True

    def _segarkan_bawah(self, d, jalan, ada):
        # Panel fatigue besar
        if jalan:
            status = d["fatigue"]
            self._set(self.lbl_fatigue, NAMA_FATIGUE.get(status, status), WARNA_FATIGUE.get(status, TEKS_PUDAR))
            self._set(self.lbl_pesan, PESAN_FATIGUE.get(status, ""))
        else:
            self._set(self.lbl_fatigue, "-", TEKS)
            self._set(self.lbl_pesan, "Mulai monitoring untuk melihat indikator fatigue.")

        # Grafik kedip: 1 sampel per detik
        if ada and time.time() - self._sampel_terakhir >= 1:
            self.riwayat_kedip.append(d["kedip_per_menit"])
            self._sampel_terakhir = time.time()
            self._gambar_grafik()

        # Jarak
        judul, warna, ket, progres = self._status_jarak(d, jalan, ada)
        self._set(self.lbl_jarak, judul, warna)
        self._set(self.lbl_rasio, ket)
        kunci = (round(progres, 2), judul)
        if self._progres_terakhir != kunci:
            self._progres_terakhir = kunci
            self.progres_jarak.configure(progress_color=MERAH if judul == "Terlalu dekat" else BIRU)
            self.progres_jarak.set(progres)
        sisa = d["sisa_kunci"] if ada else None
        self._set(self.lbl_sisa, f"Kunci layar dalam {sisa:.0f} dtk" if sisa is not None else "")

        # Peringatan
        daftar = self.monitor.ambil_peringatan()[-5:]
        teks = "\n".join(f"{jam}   {pesan}" for jam, pesan in reversed(daftar))
        self._set(self.lbl_peringatan, teks or "Belum ada peringatan.")

    def _gambar_grafik(self):
        c = self.canvas
        c.delete("all")
        w, h = LEBAR_GRAFIK, TINGGI_GRAFIK
        nilai = list(self.riwayat_kedip)
        puncak = max(20, max(nilai, default=0) * 1.1)

        def y(v):
            return h - 8 - (v / puncak) * (h - 16)

        batas = y(config.KEDIP_MIN_PER_MENIT)
        c.create_line(0, batas, w, batas, fill=MERAH, dash=(5, 4))
        if len(nilai) >= 2:
            langkah = w / (len(nilai) - 1)
            titik = []
            for i, v in enumerate(nilai):
                titik += [i * langkah, y(v)]
            c.create_line(*titik, fill=BIRU, width=3, smooth=True)