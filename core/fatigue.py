import time
from collections import deque
import config


class FatigueDetector:
    def __init__(self):
        self.mulai = time.time()
        self.waktu_kedip = deque() 
        self.jumlah_kedip_lalu = 0
        self.mulai_tertutup = None
        self.kedip_per_menit = 0.0
        self.status = "Mengumpulkan data..."

    def perbarui(self, tertutup, jumlah_kedip):
        sekarang = time.time()

        if jumlah_kedip > self.jumlah_kedip_lalu:
            self.waktu_kedip.append(sekarang)
        self.jumlah_kedip_lalu = jumlah_kedip

        while self.waktu_kedip and sekarang - self.waktu_kedip[0] > config.JENDELA_KEDIP:
            self.waktu_kedip.popleft()

        if tertutup:
            if self.mulai_tertutup is None:
                self.mulai_tertutup = sekarang
            lama_tertutup = sekarang - self.mulai_tertutup
        else:
            self.mulai_tertutup = None
            lama_tertutup = 0

        lama_data = min(sekarang - self.mulai, config.JENDELA_KEDIP)
        if lama_data > 0:
            self.kedip_per_menit = len(self.waktu_kedip) * 60 / lama_data

        # Tentukan status
        if lama_tertutup > config.DURASI_MENGANTUK:
            self.status = "Mengantuk"
        elif sekarang - self.mulai < config.DURASI_DATA_FATIGUE:
            self.status = "Mengumpulkan data..."
        elif self.kedip_per_menit < config.KEDIP_MIN_PER_MENIT:
            self.status = "Lelah"
        else:
            self.status = "Normal"

    def reset(self):
        self.mulai_tertutup = None