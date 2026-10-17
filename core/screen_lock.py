import ctypes
import time
import config


class ScreenLocker:
    def __init__(self):
        self.aktif = False          
        self.mulai_dekat = None    
        self.terakhir_kunci = 0.0    
        self.sisa = None          

    def ubah_aktif(self):
        self.aktif = not self.aktif
        self.mulai_dekat = None
        self.sisa = None

    def perbarui(self, terlalu_dekat):
        sekarang = time.time()

        if not terlalu_dekat:
            self.mulai_dekat = None
            self.sisa = None
            return False

        if self.mulai_dekat is None:
            self.mulai_dekat = sekarang

        lama = sekarang - self.mulai_dekat
        self.sisa = max(0, config.DURASI_KUNCI_DETIK - lama)

        if not self.aktif:
            return False

        sudah_jeda = sekarang - self.terakhir_kunci > config.JEDA_SETELAH_KUNCI
        if lama >= config.DURASI_KUNCI_DETIK and sudah_jeda:
            self.kunci()
            self.terakhir_kunci = sekarang
            self.mulai_dekat = None
            self.sisa = None
            return True
        return False

    def kunci(self):
        ctypes.windll.user32.LockWorkStation()

    def reset(self):
        self.mulai_dekat = None
        self.sisa = None
