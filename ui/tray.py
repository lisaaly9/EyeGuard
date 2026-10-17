"""Ikon di system tray Windows."""
import pystray
from PIL import Image, ImageDraw


def buat_ikon():
    gambar = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    g = ImageDraw.Draw(gambar)
    g.rounded_rectangle((2, 2, 62, 62), radius=16, fill="#1F5FE0")
    g.ellipse((10, 21, 54, 43), outline="white", width=4)
    g.ellipse((26, 26, 38, 38), fill="white")
    return gambar


class Tray:
    def __init__(self, perintah):
        """perintah: fungsi yang dipanggil dengan nama perintah (dari thread tray)."""
        menu = pystray.Menu(
            pystray.MenuItem("Buka dashboard", lambda: perintah("buka"), default=True),
            pystray.MenuItem("Mulai / hentikan monitoring", lambda: perintah("toggle")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Keluar", lambda: perintah("keluar")),
        )
        self.ikon = pystray.Icon("EyeGuard", buat_ikon(), "EyeGuard", menu)

    def mulai(self):
        self.ikon.run_detached()

    def notifikasi(self, teks):
        try:
            self.ikon.notify(teks, "EyeGuard")
        except Exception:
            pass

    def berhenti(self):
        self.ikon.stop()
