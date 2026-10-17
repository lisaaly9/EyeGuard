"""Kotak merah di pojok kanan bawah layar saat pengguna terlalu dekat."""
import tkinter as tk
import winsound

from ui.tema import MERAH


class PopupPeringatan:
    def __init__(self, jendela):
        self.jendela = jendela
        self.kotak = None      # jendela pop-up, None kalau sedang tidak tampil
        self.label = None

    def perbarui(self, data, ada_wajah):
        """Tampilkan pop-up kalau terlalu dekat, tutup kalau sudah aman."""
        if ada_wajah and data["terlalu_dekat"]:
            if self.kotak is None:
                self._buat()
            teks = "Terlalu dekat dengan layar!\nMundur sedikit ya."
            sisa = data["sisa_kunci"]
            if data["kunci_aktif"] and sisa is not None:
                teks += f"\nLayar dikunci dalam {sisa:.0f} detik"
            if self.label.cget("text") != teks:
                self.label.configure(text=teks)
        else:
            self.tutup()

    def tutup(self):
        if self.kotak is not None:
            self.kotak.destroy()
            self.kotak = None

    def _buat(self):
        kotak = tk.Toplevel(self.jendela)
        kotak.overrideredirect(True)           # tanpa bingkai jendela
        kotak.attributes("-topmost", True)     # selalu di atas aplikasi lain
        kotak.configure(bg=MERAH)
        lebar, tinggi = 340, 120
        x = self.jendela.winfo_screenwidth() - lebar - 24
        y = self.jendela.winfo_screenheight() - tinggi - 90
        kotak.geometry(f"{lebar}x{tinggi}+{x}+{y}")
        self.label = tk.Label(kotak, text="", bg=MERAH, fg="white",
                              font=("Segoe UI", 14, "bold"), justify="center")
        self.label.pack(expand=True, fill="both", padx=12, pady=12)
        self.kotak = kotak
        winsound.MessageBeep()
