# AutoAbsen Maganghub + OpenRouter AI

Otomatisasi pembuatan dan pengisian laporan harian Maganghub dengan arsitektur berlapis (core/service/infrastructure).

## Fitur Utama
- Generate konten laporan harian menggunakan OpenRouter AI.
- Submit otomatis ke portal Maganghub menggunakan SeleniumBase.
- Dukungan 3 mode eksekusi:
`CLI manual`, `Telegram bot long-running`, `Telegram workflow short-lived` (cocok untuk scheduler CI).
- Dukungan automasi presensi eksternal terpisah (isi form + klik tombol) tanpa trigger user.
- Konfigurasi tervalidasi via `pydantic-settings`.

## Struktur Project
```text
src/
├── core/                       # Entity + interface domain
├── services/                   # Orkestrasi use case (ReportService)
├── infrastructure/
│   ├── ai/                     # Adapter OpenRouter
│   ├── automation/             # Adapter SeleniumBase + selector
│   ├── integrations/           # Adapter integrasi eksternal (mis. notifier Telegram)
│   └── telegram/               # Handler bot Telegram
├── main.py                     # Entry CLI manual
├── bot_runner.py               # Entry bot Telegram long-running
├── workflow_runner.py          # Entry workflow Telegram short-lived (CI)
└── external_presensi_runner.py # Entry presensi eksternal terpisah
```

## Prasyarat
- Python 3.9+
- Google Chrome / Chromium
- Akun Maganghub valid
- API key OpenRouter
- (Opsional) Telegram bot token untuk mode bot/workflow

## Instalasi
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Konfigurasi `.env`
Minimal untuk mode CLI:
```env
MAGANGHUB_EMAIL=your_email@example.com
MAGANGHUB_PASSWORD=your_password
OPENROUTER_API_KEY=sk-or-v1-...
AI_MODEL=openai/gpt-4o-mini
AKTIVITAS_KONTEKS=Deskripsi konteks magang
SHOW_BROWSER=true
```

Tambahan untuk mode Telegram:
```env
TELEGRAM_BOT_TOKEN=123456:ABCDEF...
ALLOWED_TELEGRAM_ID=123456789
```

Tambahan untuk automasi presensi eksternal terpisah:
```env
PRESENSI_ENABLED=true
PRESENSI_URL=https://script.google.com/macros/s/.../exec
PRESENSI_FULL_NAME=Made Dhyo Pradnyadiva
PRESENSI_UNIT=Pengembangan Aplikasi
PRESENSI_ACTION=MASUK
PRESENSI_SHOW_BROWSER=false
```

Kompatibilitas lama:
- `HEADLESS_MODE=true` masih didukung; akan dipetakan menjadi `SHOW_BROWSER=false`.

## Cara Menjalankan
Mode CLI manual:
```bash
python src/main.py
```

Mode Telegram bot long-running:
```bash
python src/bot_runner.py
```

Mode workflow short-lived (mis. dari GitHub Actions):
```bash
python src/workflow_runner.py
```

Mode presensi eksternal terpisah (manual trigger):
```bash
python src/external_presensi_runner.py
```

## Deploy
- Lihat `DEPLOYMENT.md` untuk detail deployment GitHub Actions, VPS, dan container.
- Workflow schedule bawaan: `.github/workflows/daily_absen.yml`.
- Workflow presensi eksternal terpisah: `.github/workflows/external_presensi.yml`.
  Workflow ini dijadwalkan otomatis:
  1) 06:15 WITA untuk aksi `MASUK` (cron UTC: `15 22 * * *`)
  2) 16:00 WITA untuk aksi `KELUAR` (cron UTC: `0 8 * * *`)

## Catatan Teknis
- Jika UI Maganghub berubah, update selector di `src/infrastructure/automation/selectors.py`.
- Validasi laporan domain memakai minimum panjang karakter terpusat di `src/core/entities.py`.

## Kode Log Troubleshooting (Maganghub)
Gunakan kode ini untuk cepat identifikasi titik gagal di GitHub Actions log:

| Kode | Arti |
|---|---|
| `WF-CONFIG-ERR` | Secret Telegram untuk workflow tidak lengkap. |
| `WF-NOTIFY-ERR` | Gagal kirim reminder awal ke Telegram. |
| `WF-GEN-ERR` | Gagal generate draft laporan dari AI. |
| `WF-TIMEOUT` | Tidak ada interaksi user sampai batas waktu 15 menit. |
| `WF-SUBMIT-EXCEPTION` | Ada exception saat proses submit report. |
| `WF-SUBMIT-ERR` | Submit selesai tapi hasilnya gagal (false). |
| `MH-DRIVER-START-ERR` | Browser Selenium gagal start. |
| `MH-LOGIN-ERR-REJECTED` | Kredensial ditolak oleh halaman login. |
| `MH-LOGIN-ERR-TIMEOUT` | Login tidak lanjut ke dashboard dalam batas waktu. |
| `MH-NAV-ERR` | Gagal buka dialog laporan hari ini dari kalender. |
| `MH-FILL-ERR-TEXTAREA` | Field textarea laporan tidak ditemukan/kurang dari 3. |
| `MH-FILL-LEN-RETRY` | Panjang field belum valid setelah fill pertama, bot mencoba isi ulang via `send_keys`. |
| `MH-FILL-ERR-LEN` | Setelah diisi, panjang field masih di bawah minimal UI (100 karakter). |
| `MH-FILL-ERR-CHECKBOX` | Checkbox konfirmasi tidak berhasil dicentang. |
| `MH-FILL-SUBMIT-LOCKED` | Setelah fill + checkbox, tombol submit masih disabled (indikasi ada field required lain). |
| `MH-FILL-ATTENDANCE` | Hasil deteksi/penyetelan field kehadiran ke nilai `Hadir`. |
| `MH-FILL-ATTENDANCE-OK` | Field kehadiran terkonfirmasi `Hadir`. |
| `MH-FILL-ATTENDANCE-WARN` | Bot belum bisa konfirmasi field kehadiran `Hadir` sebelum submit phase. |
| `MH-SUBMIT-WAIT` | Kandidat tombol submit belum siap (masih disabled) atau belum terdeteksi di dialog aktif. |
| `MH-SUBMIT-CLICK` | Bot sudah melakukan klik tombol submit. |
| `MH-SUBMIT-PENDING` | Setelah klik submit, dialog masih terbuka dan bot melaporkan feedback validasi sementara. |
| `MH-SUBMIT-RETRY` | Bot mencoba klik submit ulang karena tombol masih enabled tetapi dialog belum menutup. |
| `MH-SUBMIT-ERR-DETAIL` | Ringkasan feedback error/validasi dari dialog saat submit gagal. |
| `MH-SUBMIT-ERR-BUTTON` | Tombol submit tidak ditemukan dalam kondisi enabled. |
| `MH-SUBMIT-ERR-CHECKBOX` | Submit diblokir karena checkbox konfirmasi masih unchecked. |
| `MH-SUBMIT-ERR-DIALOG` | Setelah klik submit, dialog tidak menutup (indikasi submit gagal). |

## Disclaimer
Gunakan alat ini secara bertanggung jawab dan isi laporan sesuai aktivitas nyata.
