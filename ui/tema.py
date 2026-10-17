"""Hal-hal yang dipakai bersama oleh semua halaman: warna, teks fatigue, dan pembuat tampilan."""
from datetime import datetime

import customtkinter as ctk

# warna
BIRU = "#1F5FE0"
BIRU_GELAP = "#1A4FC0"      # saat tombol ditunjuk mouse
BIRU_MUDA = "#E6EEFF"
LATAR = "#F1F6FF"
GARIS = "#DCE7FA"
GARIS_TOMBOL = "#9DB6F0"
TEKS = "#0F2552"
TEKS_PUDAR = "#4A5D80"
HIJAU = "#137A48"
AMBER = "#8A5300"
MERAH = "#C0392B"

# teks untuk tiap status fatigue
WARNA_FATIGUE = {"Normal": HIJAU, "Lelah": AMBER, "Mengantuk": MERAH}
NAMA_FATIGUE = {"Mengumpulkan data...": "Menunggu data"}
KET_FATIGUE = {
    "Normal": "Kondisi baik",
    "Lelah": "Kedip rendah",
    "Mengantuk": "Mata tertutup lama",
    "Mengumpulkan data...": "30 detik pertama",
}
PESAN_FATIGUE = {
    "Normal": "Kondisi mata baik. Tetap berkedip secara teratur.",
    "Lelah": "Istirahatkan mata dan tatap objek jauh selama 20 detik.",
    "Mengantuk": "Mata tertutup cukup lama. Istirahatlah sejenak.",
    "Mengumpulkan data...": "Butuh sekitar 30 detik data untuk menilai kondisi mata.",
}


def buat_font():
    """Harus dipanggil setelah jendela dibuat. Mengembalikan (judul, besar, fatigue, tebal, kecil)."""
    return (ctk.CTkFont(size=24, weight="bold"),
            ctk.CTkFont(size=26, weight="bold"),
            ctk.CTkFont(size=34, weight="bold"),
            ctk.CTkFont(size=15, weight="bold"),
            ctk.CTkFont(size=13))


def buat_kartu(parent):
    """Kotak putih dengan sudut membulat."""
    return ctk.CTkFrame(parent, fg_color="white", corner_radius=16,
                        border_width=1, border_color=GARIS)


def tombol_biru(parent, teks, perintah):
    return ctk.CTkButton(parent, text=teks, height=40, corner_radius=12,
                         fg_color=BIRU, hover_color=BIRU_GELAP, command=perintah)


def tombol_garis(parent, teks, perintah):
    """Tombol putih dengan garis tepi biru."""
    return ctk.CTkButton(parent, text=teks, height=40, corner_radius=12,
                         fg_color="white", text_color=BIRU, border_width=2,
                         border_color=GARIS_TOMBOL, hover_color=BIRU_MUDA, command=perintah)


def format_durasi(detik):
    detik = int(detik)
    jam, sisa = divmod(detik, 3600)
    menit, dtk = divmod(sisa, 60)
    if jam:
        return f"{jam} j {menit:02d} mnt"
    if menit:
        return f"{menit} mnt {dtk:02d} dtk"
    return f"{dtk} dtk"


def format_waktu(teks):
    """'2026-10-16 11:54:08' menjadi '16/10/2026 11:54'."""
    try:
        return datetime.strptime(teks, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return teks or "-"
