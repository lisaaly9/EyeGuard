import cv2
import config

class Camera:
    def __init__(self, nomor=config.NOMOR_KAMERA):
        self.nomor = nomor
        self.cap = None

    def buka(self):
        self.cap = cv2.VideoCapture(self.nomor, cv2.CAP_DSHOW)
        return self.cap.isOpened()

    def ambil_frame(self):
        if self.cap is None:
            return None
        berhasil, frame = self.cap.read()
        if not berhasil:
            return None
        return cv2.flip(frame, 1)

    def tutup(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None