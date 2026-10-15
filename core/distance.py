import math
import config


class DistanceEstimator:
    def __init__(self):
        self.lebar_patokan = None  
        self.lebar_sekarang = 0.0
        self.rasio = 0.0

    def hitung_lebar(self, titik):
        return math.dist(titik[config.TITIK_WAJAH_KIRI],
                         titik[config.TITIK_WAJAH_KANAN])

    def kalibrasi(self, titik):
        self.lebar_patokan = self.hitung_lebar(titik)

    def sudah_kalibrasi(self):
        return self.lebar_patokan is not None

    def analisis(self, titik):
        self.lebar_sekarang = self.hitung_lebar(titik)
        if self.sudah_kalibrasi():
            self.rasio = self.lebar_sekarang / self.lebar_patokan

    def terlalu_dekat(self):
        return self.sudah_kalibrasi() and self.rasio >= config.RASIO_TERLALU_DEKAT