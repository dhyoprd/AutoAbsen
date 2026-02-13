# Refactor Todo (Completed)

- [x] Konsistenkan kontrak `IAutomationDriver` agar `ReportService` tidak bergantung pada concrete type check.
- [x] Implementasikan method interface di `SeleniumBaseDriver` (bukan `pass`) dan rapikan lifecycle browser session.
- [x] Sentralisasi aturan validasi panjang konten pada domain entity (`Report`) dan sinkronkan adapter AI/prompt.
- [x] Terapkan best practice konfigurasi `pydantic-settings` untuk kompatibilitas env lama (`HEADLESS_MODE`) dan env utama (`SHOW_BROWSER`).
- [x] Aktifkan allowlist enforcement pada Telegram bot long-running (`ALLOWED_TELEGRAM_ID`).
- [x] Sinkronkan dokumentasi (`README.md`, `README_MACOS.md`, `DEPLOYMENT.md`, `.env.example`) dengan struktur dan command aktual.
- [x] Jalankan validasi sintaks source project setelah refactor.

# Schedule Patch Todo (15:30 WITA)

- [x] Ubah cron ke 15:30 WITA (`07:30 UTC`) di workflow schedule.
- [x] Tambahkan langkah observability (`Show Trigger Context`) untuk debug jadwal.
- [x] Hapus install Chrome manual yang rawan gagal dan ganti verifikasi binary browser.
- [x] Tambahkan validasi required secrets agar gagal cepat dengan pesan yang jelas.
- [x] Siapkan checklist verifikasi pasca-deploy lewat `workflow_dispatch` dan run schedule berikutnya.
