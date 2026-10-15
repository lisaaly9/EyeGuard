import cv2
from core.camera import Camera
from core.face_detector import FaceDetector, MATA_KIRI, MATA_KANAN
from core.eye_analyzer import EyeAnalyzer
from core.distance import DistanceEstimator
from core.screen_lock import ScreenLocker
from core.fatigue import FatigueDetector


def gambar_mata(frame, titik):
    for nomor in MATA_KIRI + MATA_KANAN:
        cv2.circle(frame, titik[nomor], 2, (0, 255, 0), -1)


def main():
    kamera = Camera()
    detektor = FaceDetector()
    analisis = EyeAnalyzer()
    jarak = DistanceEstimator()
    kunci = ScreenLocker()
    fatigue = FatigueDetector()

    if not kamera.buka():
        print("Gagal membuka kamera")
        return
    print("Kamera berhasil dibuka. 'c' = kalibrasi, 'l' = kunci layar on/off, 'q' = keluar.")

    while True:
        frame = kamera.ambil_frame()
        if frame is None:
            print("Gagal mengambil gambar dari kamera")
            break

        titik = detektor.deteksi(frame)
        tombol = cv2.waitKey(1) & 0xFF

        if tombol == ord('l'):
            kunci.ubah_aktif()
            print("Kunci layar:", "AKTIF" if kunci.aktif else "MATI")

        if titik is None:
            analisis.reset_frame()
            kunci.reset()
            cv2.putText(frame, "Wajah tidak terdeteksi", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        else:
            gambar_mata(frame, titik)
            analisis.analisis(titik, MATA_KIRI, MATA_KANAN)
            jarak.analisis(titik)

            if tombol == ord('c'):
                jarak.kalibrasi(titik)
                print("Kalibrasi tersimpan.")

            # Status mata
            if analisis.tertutup:
                status, warna = "Mata tertutup", (0, 0, 255)
            else:
                status, warna = "Mata terbuka", (0, 255, 0)
            cv2.putText(frame, status, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, warna, 2)
            cv2.putText(frame, f"EAR: {analisis.ear:.2f}", (20, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Kedip: {analisis.jumlah_kedip}", (20, 105),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Indikator fatigue
            fatigue.perbarui(analisis.tertutup, analisis.jumlah_kedip)
            if fatigue.status == "Normal":
                warna_f = (0, 255, 0)
            elif fatigue.status == "Mengumpulkan data...":
                warna_f = (0, 255, 255)
            else:
                warna_f = (0, 0, 255)
            cv2.putText(frame, f"Fatigue: {fatigue.status}", (20, 210),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, warna_f, 2)
            cv2.putText(frame, f"Kedip/menit: {fatigue.kedip_per_menit:.0f}", (20, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Status jarak
            if not jarak.sudah_kalibrasi():
                teks_jarak, warna_jarak = "Jarak: tekan 'c' untuk kalibrasi", (0, 255, 255)
            elif jarak.terlalu_dekat():
                teks_jarak, warna_jarak = f"Jarak: TERLALU DEKAT ({jarak.rasio:.2f}x)", (0, 0, 255)
            else:
                teks_jarak, warna_jarak = f"Jarak: Normal ({jarak.rasio:.2f}x)", (0, 255, 0)
            cv2.putText(frame, teks_jarak, (20, 140),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, warna_jarak, 2)

            # Timer dan kunci layar
            baru_dikunci = kunci.perbarui(jarak.terlalu_dekat())
            if baru_dikunci:
                print("Layar dikunci.")

            if kunci.sisa is not None:
                cv2.putText(frame, f"Kunci layar dalam: {kunci.sisa:.0f} dtk", (20, 175),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        teks_kunci = "Kunci layar: AKTIF" if kunci.aktif else "Kunci layar: MATI ('l')"
        cv2.putText(frame, teks_kunci, (20, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("EyeGuard - Kamera", frame)

        if tombol == ord('q'):
            break

    detektor.tutup()
    kamera.tutup()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()