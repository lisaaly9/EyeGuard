import cv2
import mediapipe as mp

MATA_KIRI = [362, 385, 387, 263, 373, 380]
MATA_KANAN = [33, 160, 158, 133, 153, 144]


class FaceDetector:
    def __init__(self):
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def deteksi(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hasil = self.mesh.process(rgb)

        if not hasil.multi_face_landmarks:
            return None

        tinggi, lebar = frame.shape[:2]
        titik = hasil.multi_face_landmarks[0].landmark
        return [(int(p.x * lebar), int(p.y * tinggi)) for p in titik]

    def tutup(self):
        self.mesh.close()
