import hashlib
import hmac
import os
import re
import sqlite3
import time
from contextlib import contextmanager
import config

PATH_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eyeguard.db")

BATAS = {
    "AMBANG_EAR": (0.10, 0.35, "Ambang EAR"),
    "RASIO_TERLALU_DEKAT": (1.05, 2.0, "Rasio terlalu dekat"),
    "DURASI_KUNCI_DETIK": (5, 300, "Durasi sebelum kunci layar"),
    "KEDIP_MIN_PER_MENIT": (3, 20, "Kedip minimum per menit"),
    "DURASI_MENGANTUK": (0.5, 5.0, "Durasi mata tertutup (mengantuk)"),
}

DEFAULT = {nama: getattr(config, nama) for nama in BATAS}


@contextmanager
def _db():
    k = sqlite3.connect(PATH_DB)
    k.row_factory = sqlite3.Row
    try:
        yield k
        k.commit()
    finally:
        k.close()


def buat_tabel():
    with _db() as k:
        k.executescript("""
            CREATE TABLE IF NOT EXISTS tbl_threshold (
                nama  TEXT PRIMARY KEY,
                nilai REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tbl_monitoring (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                waktu_mulai        TEXT,
                waktu_selesai      TEXT,
                durasi_detik       INTEGER,
                total_kedip        INTEGER,
                kedip_per_menit    REAL,
                kali_terlalu_dekat INTEGER,
                kali_dikunci       INTEGER,
                status_fatigue     TEXT
            );
            CREATE TABLE IF NOT EXISTS tbl_peringatan (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                id_monitoring INTEGER REFERENCES tbl_monitoring(id),
                waktu         TEXT,
                pesan         TEXT
            );
            CREATE TABLE IF NOT EXISTS tbl_pengguna (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nama          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                dibuat_pada   TEXT
            );
        """)


# --- threshold ---
def muat_ke_config():
    with _db() as k:
        for baris in k.execute("SELECT nama, nilai FROM tbl_threshold"):
            nama = baris["nama"]
            if nama in BATAS:
                setattr(config, nama, type(DEFAULT[nama])(baris["nilai"]))


def ambil_threshold():
    return {nama: getattr(config, nama) for nama in BATAS}


def validasi_threshold(nilai):
    for nama, v in nilai.items():
        if nama not in BATAS:
            continue
        minimum, maksimum, label = BATAS[nama]
        try:
            v = float(v)
        except (TypeError, ValueError):
            return False, f"{label} harus berupa angka."
        if not (minimum <= v <= maksimum):
            return False, f"{label} harus antara {minimum} dan {maksimum}."
    return True, ""


def simpan_threshold(nilai):
    ok, pesan = validasi_threshold(nilai)
    if not ok:
        return False, pesan
    with _db() as k:
        for nama, v in nilai.items():
            if nama not in BATAS:
                continue
            v = type(DEFAULT[nama])(float(v))
            k.execute("INSERT OR REPLACE INTO tbl_threshold (nama, nilai) VALUES (?, ?)", (nama, v))
            setattr(config, nama, v)
    return True, "Threshold berhasil disimpan."


def reset_threshold():
    with _db() as k:
        k.execute("DELETE FROM tbl_threshold")
    for nama, v in DEFAULT.items():
        setattr(config, nama, v)


def simpan_sesi(ringkasan, peringatan):
    with _db() as k:
        cur = k.execute(
            """INSERT INTO tbl_monitoring
               (waktu_mulai, waktu_selesai, durasi_detik, total_kedip, kedip_per_menit,
                kali_terlalu_dekat, kali_dikunci, status_fatigue)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ringkasan["waktu_mulai"], time.strftime("%Y-%m-%d %H:%M:%S"),
             ringkasan["durasi_detik"], ringkasan["total_kedip"], ringkasan["kedip_per_menit"],
             ringkasan["kali_terlalu_dekat"], ringkasan["kali_dikunci"],
             ringkasan["status_fatigue"]),
        )
        id_sesi = cur.lastrowid
        k.executemany(
            "INSERT INTO tbl_peringatan (id_monitoring, waktu, pesan) VALUES (?, ?, ?)",
            [(id_sesi, waktu, pesan) for waktu, pesan in peringatan],
        )
    return id_sesi


def ambil_riwayat(batas=50):
    with _db() as k:
        return [dict(b) for b in k.execute(
            "SELECT * FROM tbl_monitoring ORDER BY id DESC LIMIT ?", (batas,))]


def ambil_peringatan(id_sesi):
    with _db() as k:
        return [dict(b) for b in k.execute(
            "SELECT waktu, pesan FROM tbl_peringatan WHERE id_monitoring = ? ORDER BY id",
            (id_sesi,))]


def ringkasan_total():
    with _db() as k:
        b = k.execute(
            """SELECT COUNT(*) AS jumlah_sesi,
                      COALESCE(SUM(durasi_detik), 0) AS total_durasi,
                      COALESCE(AVG(kedip_per_menit), 0) AS rata_kedip,
                      COALESCE(SUM(kali_terlalu_dekat), 0) AS total_dekat
               FROM tbl_monitoring"""
        ).fetchone()
    return dict(b)


# --- akun pengguna ---
def _hash_password(password, garam=None):
    garam = garam or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), garam.encode("utf-8"), 100_000).hex()
    return f"{garam}${digest}"


def _cek_password(password, tersimpan):
    try:
        garam, _ = tersimpan.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(_hash_password(password, garam), tersimpan)


def validasi_registrasi(nama, email, password):
    nama = (nama or "").strip()
    email = (email or "").strip().lower()
    if len(nama) < 3:
        return False, "Nama minimal 3 karakter."
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Format email tidak valid."
    if len(password or "") < 6:
        return False, "Password minimal 6 karakter."
    with _db() as k:
        ada = k.execute("SELECT 1 FROM tbl_pengguna WHERE email = ?", (email,)).fetchone()
    if ada:
        return False, "Email sudah terdaftar."
    return True, ""


def daftar_pengguna(nama, email, password):
    ok, pesan = validasi_registrasi(nama, email, password)
    if not ok:
        return False, pesan, None
    nama, email = nama.strip(), email.strip().lower()
    with _db() as k:
        cur = k.execute(
            "INSERT INTO tbl_pengguna (nama, email, password_hash, dibuat_pada) VALUES (?, ?, ?, ?)",
            (nama, email, _hash_password(password), time.strftime("%Y-%m-%d %H:%M:%S")),
        )
    return True, "Registrasi berhasil.", cur.lastrowid


def login_pengguna(email, password):
    email = (email or "").strip().lower()
    with _db() as k:
        baris = k.execute("SELECT * FROM tbl_pengguna WHERE email = ?", (email,)).fetchone()
    if baris is None or not _cek_password(password or "", baris["password_hash"]):
        return False, "Email atau password salah.", None
    return True, "", dict(baris)