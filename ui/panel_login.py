import customtkinter as ctk
from data import database
from ui.tema import BIRU, GARIS, MERAH, TEKS, TEKS_PUDAR, buat_kartu, tombol_biru

SCRIM = "#0B1B3F"


class PanelLogin(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=SCRIM, corner_radius=0)
        self._setelah_masuk = None
        self._mode_daftar = False

        f_judul = ctk.CTkFont(size=20, weight="bold")
        f_kecil = ctk.CTkFont(size=12)

        kartu = buat_kartu(self)
        kartu.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkButton(kartu, text="✕", width=28, height=28, corner_radius=14,
                     fg_color="transparent", text_color=TEKS_PUDAR,
                     hover_color=GARIS, command=self.sembunyikan
                     ).place(relx=1.0, x=-10, y=10, anchor="ne")

        self.lbl_judul = ctk.CTkLabel(kartu, text="Masuk ke EyeGuard", font=f_judul, text_color=TEKS)
        self.lbl_judul.pack(pady=(28, 4), padx=60)
        ctk.CTkLabel(kartu, text="Masuk dulu sebelum mulai monitoring.", font=f_kecil, text_color=TEKS_PUDAR).pack(pady=(0, 16))

        self.entri_nama = ctk.CTkEntry(kartu, placeholder_text="Nama lengkap", height=38, width=260)
        self.entri_email = ctk.CTkEntry(kartu, placeholder_text="Email", height=38, width=260)
        self.entri_password = ctk.CTkEntry(kartu, placeholder_text="Password", show="•", height=38, width=260)
        self.entri_email.pack(padx=24, pady=5)
        self.entri_password.pack(padx=24, pady=5)

        self.lbl_pesan = ctk.CTkLabel(kartu, text="", font=f_kecil, text_color=MERAH, wraplength=260)
        self.lbl_pesan.pack(pady=(4, 0))

        self.btn_aksi = tombol_biru(kartu, "Masuk", self._submit)
        self.btn_aksi.pack(fill="x", padx=24, pady=(14, 6))

        self.btn_ganti = ctk.CTkButton(kartu, text="Belum punya akun? Daftar", fg_color="transparent", text_color=BIRU, hover_color="white", command=self._ganti_mode)
        self.btn_ganti.pack(pady=(0, 24))

        self.entri_password.bind("<Return>", lambda e: self._submit())

    def tampilkan(self, setelah_masuk=None):
        self._setelah_masuk = setelah_masuk
        if self._mode_daftar:
            self._ganti_mode()
        self.lbl_pesan.configure(text="")
        self.entri_email.delete(0, "end")
        self.entri_password.delete(0, "end")
        self.entri_nama.delete(0, "end")
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self.entri_email.focus_set()

    def sembunyikan(self):
        self.place_forget()

    def _ganti_mode(self):
        self._mode_daftar = not self._mode_daftar
        self.lbl_pesan.configure(text="")
        if self._mode_daftar:
            self.lbl_judul.configure(text="Daftar akun baru")
            self.entri_nama.pack(padx=24, pady=5, before=self.entri_email)
            self.btn_aksi.configure(text="Daftar")
            self.btn_ganti.configure(text="Sudah punya akun? Masuk")
        else:
            self.lbl_judul.configure(text="Masuk ke EyeGuard")
            self.entri_nama.pack_forget()
            self.btn_aksi.configure(text="Masuk")
            self.btn_ganti.configure(text="Belum punya akun? Daftar")

    def _submit(self):
        email = self.entri_email.get()
        password = self.entri_password.get()
        if self._mode_daftar:
            nama = self.entri_nama.get()
            ok, pesan, id_pengguna = database.daftar_pengguna(nama, email, password)
            if not ok:
                self.lbl_pesan.configure(text=pesan)
                return
            pengguna = {"id": id_pengguna, "nama": nama.strip(), "email": email.strip().lower()}
        else:
            ok, pesan, pengguna = database.login_pengguna(email, password)
            if not ok:
                self.lbl_pesan.configure(text=pesan)
                return
        self.sembunyikan()
        self.master._login_berhasil(pengguna, self._setelah_masuk)