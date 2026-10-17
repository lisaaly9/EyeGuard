import threading
import time
import cv2
from core.camera import Camera
from core.face_detector import FaceDetector, MATA_KIRI, MATA_KANAN
from core.eye_analyzer import EyeAnalyzer
from core.distance import DistanceEstimator
from core.screen_lock import ScreenLocker
from core.fatigue import FatigueDetector
from data import database

MAKS_PERINGATAN = 20

class Monitor:
    def __init__(self):
        self.kamera = Camera()
        self.jarak = DistanceEstimator()
        self.kunci = ScreenLocker()

        self.analisis = EyeAnalyzer()
        self.fatigue = FatigueDetector()

        self._gembok = threading.Lock()
        self._thread = None
        self._jalan = False
        self._minta_kalibrasi = False
        self._frame = None
        self._peringatan = []          
        self._peringatan_sesi = []    
        self._catat_terakhir = {}
        self._data = self._data_kosong()

        self._dekat_lalu = False
        self._fatigue_lalu = ""
        self.waktu_mulai = time.time()
        self.waktu_mulai_teks = ""
        self.jumlah_terlalu_dekat = 0
        self.jumlah_dikunci = 0

 
    def mulai(self):
        if self._jalan:
            return True
        if not self.kamera.buka():
            self._catat("Kamera tidak bisa dibuka")
            return False

        self.analisis = EyeAnalyzer()
        self.fatigue = FatigueDetector()
        self.kunci.reset()
        self._dekat_lalu = False
        self._fatigue_lalu = ""
        self.waktu_mulai = time.time()
        self.waktu_mulai_teks = time.strftime("%Y-%m-%d %H:%M:%S")
        self.jumlah_terlalu_dekat = 0
        self.jumlah_dikunci = 0
        self._peringatan_sesi = []

        with self._gembok:
            self._data = self._data_kosong()
            self._data["berjalan"] = True

        self._jalan = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def berhenti(self):
        self._jalan = False
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None

    def kalibrasi(self):
        self._minta_kalibrasi = True

    def ubah_kunci(self):
        self.kunci.ubah_aktif()
        return self.kunci.aktif

    def ambil_data(self):
        with self._gembok:
            return dict(self._data)

    def ambil_frame(self):
        with self._gembok:
            return None if self._frame is None else self._frame.copy()

    def ambil_peringatan(self):
        with self._gembok:
            return list(self._peringatan)

    def _data_kosong(self):
        return {
            "berjalan": False, "wajah": False, "durasi": 0,
            "ear": 0.0, "tertutup": False, "kedip": 0, "kedip_per_menit": 0.0,
            "rasio": 0.0, "sudah_kalibrasi": False, "terlalu_dekat": False,
            "sisa_kunci": None, "kunci_aktif": False,
            "fatigue": "Mengumpulkan data...",
        }

    def _catat(self, teks):
        sekarang = time.time()
        if sekarang - self._catat_terakhir.get(teks, 0) < 10:
            return  
        self._catat_terakhir[teks] = sekarang
        with self._gembok:
            self._peringatan.append((time.strftime("%H:%M"), teks))
            del self._peringatan[:-MAKS_PERINGATAN]
            self._peringatan_sesi.append((time.strftime("%H:%M:%S"), teks))

    def _simpan_sesi(self):
        durasi = int(time.time() - self.waktu_mulai)
        if durasi < 5:
            return
        with self._gembok:
            peringatan = list(self._peringatan_sesi)
        try:
            database.simpan_sesi({
                "waktu_mulai": self.waktu_mulai_teks,
                "durasi_detik": durasi,
                "total_kedip": self.analisis.jumlah_kedip,
                "kedip_per_menit": self.analisis.jumlah_kedip * 60 / durasi,
                "kali_terlalu_dekat": self.jumlah_terlalu_dekat,
                "kali_dikunci": self.jumlah_dikunci,
                "status_fatigue": self.fatigue.status,
            }, peringatan)
        except Exception as e:
            print("Gagal menyimpan riwayat:", e)

    def _loop(self):
        detektor = FaceDetector() 
        try:
            while self._jalan:
                frame = self.kamera.ambil_frame()
                if frame is None:
                    self._catat("Gagal mengambil gambar dari kamera")
                    break

                titik = detektor.deteksi(frame)
                if titik is None:
                    self._tanpa_wajah()
                else:
                    self._dengan_wajah(frame, titik)

                with self._gembok:
                    self._frame = frame
        finally:
            detektor.tutup()
            self.kamera.tutup()
            self._jalan = False
            with self._gembok:
                self._data["berjalan"] = False
            self._simpan_sesi() 

    def _tanpa_wajah(self):
        self.analisis.reset_frame()
        self.kunci.reset()
        self.fatigue.reset()
        self._dekat_lalu = False
        with self._gembok:
            self._data["wajah"] = False
            self._data["terlalu_dekat"] = False
            self._data["sisa_kunci"] = None
            self._data["durasi"] = int(time.time() - self.waktu_mulai)

    def _dengan_wajah(self, frame, titik):
        self.analisis.analisis(titik, MATA_KIRI, MATA_KANAN)
        self.jarak.analisis(titik)

        if self._minta_kalibrasi:
            self.jarak.kalibrasi(titik)
            self._minta_kalibrasi = False
            self._catat("Kalibrasi jarak tersimpan")

        dekat = self.jarak.terlalu_dekat()
        baru_dikunci = self.kunci.perbarui(dekat)
        self.fatigue.perbarui(self.analisis.tertutup, self.analisis.jumlah_kedip)

        if dekat and not self._dekat_lalu:
            self.jumlah_terlalu_dekat += 1
            self._catat("Terlalu dekat dengan layar")
        self._dekat_lalu = dekat

        status = self.fatigue.status
        if status != self._fatigue_lalu and status in ("Lelah", "Mengantuk"):
            self._catat(f"Indikator fatigue: {status}")
        self._fatigue_lalu = status

        if baru_dikunci:
            self.jumlah_dikunci += 1
            self._catat("Layar dikunci karena terlalu dekat")

        for nomor in MATA_KIRI + MATA_KANAN:
            cv2.circle(frame, titik[nomor], 2, (0, 255, 0), -1)

        with self._gembok:
            self._data.update({
                "berjalan": True, "wajah": True,
                "durasi": int(time.time() - self.waktu_mulai),
                "ear": self.analisis.ear, "tertutup": self.analisis.tertutup,
                "kedip": self.analisis.jumlah_kedip,
                "kedip_per_menit": self.fatigue.kedip_per_menit,
                "rasio": self.jarak.rasio,
                "sudah_kalibrasi": self.jarak.sudah_kalibrasi(),
                "terlalu_dekat": dekat,
                "sisa_kunci": self.kunci.sisa,
                "kunci_aktif": self.kunci.aktif,
                "fatigue": status,
            })
