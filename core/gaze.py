IRIS_KANAN_TENGAH = 468
IRIS_KIRI_TENGAH = 473

BATAS_BAWAH = 0.42
BATAS_ATAS = 0.58


def _rasio(titik, mata, iris_tengah):
    x_a = titik[mata[0]][0]
    x_b = titik[mata[3]][0]
    x_iris = titik[iris_tengah][0]
    lebar = x_b - x_a
    if lebar == 0:
        return 0.5
    return (x_iris - x_a) / lebar


def deteksi_arah(titik, mata_kiri, mata_kanan):
    r_kiri = _rasio(titik, mata_kiri, IRIS_KIRI_TENGAH)
    r_kanan = 1 - _rasio(titik, mata_kanan, IRIS_KANAN_TENGAH)
    rasio = (r_kiri + r_kanan) / 2

    if rasio < BATAS_BAWAH:
        return "Kiri"
    if rasio > BATAS_ATAS:
        return "Kanan"
    return "Tengah"