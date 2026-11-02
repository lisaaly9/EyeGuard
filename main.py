import config
from data import database
from core.monitor import Monitor
from ui.dashboard import Dashboard


def main():
    database.buat_tabel()
    database.muat_ke_config()

    monitor = Monitor()
    app = Dashboard(monitor)

    if config.MULAI_TERSEMBUNYI:
        app.sembunyikan()

    app.mainloop()
    monitor.berhenti()


if __name__ == "__main__":
    main()