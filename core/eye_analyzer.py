import math
import config


def hitung_ear(titik, indeks):
    p1, p2, p3, p4, p5, p6 = [titik[i] for i in indeks]
    tinggi = math.dist(p2, p6) + math.dist(p3, p5)
    lebar = 2 * math.dist(p1, p4)
    return tinggi / lebar


class EyeAnalyzer:
    def __init__(self):
        self.ear = 0.0
        self.tertutup = False
        self.jumlah_kedip = 0
        self.frame_tertutup = 0
        self._ear_lalu = None

    def analisis(self, titik, mata_kiri, mata_kanan):
        ear_kiri = hitung_ear(titik, mata_kiri)
        ear_kanan = hitung_ear(titik, mata_kanan)
        ear_baru = (ear_kiri + ear_kanan) / 2
        ear_min = min(ear_kiri, ear_kanan)
        self.ear = (ear_kiri + ear_kanan) / 2
        self.tertutup = min(ear_kiri, ear_kanan) < config.AMBANG_EAR
        
        if self._ear_lalu is not None and abs(ear_baru - self._ear_lalu) > 0.18:
            ear_baru = (ear_baru + self._ear_lalu) / 2
            ear_min = min(ear_min, ear_baru)
        self._ear_lalu = ear_baru
        self.ear = ear_baru
        self.tertutup = ear_min < config.AMBANG_EAR
            
        if self.tertutup:
            self.frame_tertutup += 1
        else:
            if config.FRAME_MIN_KEDIP <= self.frame_tertutup <= config.FRAME_MAX_KEDIP:
                self.jumlah_kedip += 1
            self.frame_tertutup = 0

    def reset_frame(self):
        self.frame_tertutup = 0
        self._ear_lalu = None
