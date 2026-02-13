# AutoAbsen Maganghub + OpenRouter AI

Otomatisasi pembuatan dan pengisian laporan harian Maganghub dengan arsitektur berlapis (core/service/infrastructure).

## Fitur Utama
- Generate konten laporan harian menggunakan OpenRouter AI.
- Submit otomatis ke portal Maganghub menggunakan SeleniumBase.
- Dukungan 3 mode eksekusi:
`CLI manual`, `Telegram bot long-running`, `Telegram workflow short-lived` (cocok untuk scheduler CI).
- Konfigurasi tervalidasi via `pydantic-settings`.

## Struktur Project
```text
src/
├── core/                       # Entity + interface domain
├── services/                   # Orkestrasi use case (ReportService)
├── infrastructure/
│   ├── ai/                     # Adapter OpenRouter
│   ├── automation/             # Adapter SeleniumBase + selector
│   └── telegram/               # Handler bot Telegram
├── main.py                     # Entry CLI manual
├── bot_runner.py               # Entry bot Telegram long-running
└── workflow_runner.py          # Entry workflow Telegram short-lived (CI)
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

## Deploy
- Lihat `DEPLOYMENT.md` untuk detail deployment GitHub Actions, VPS, dan container.
- Workflow schedule bawaan: `.github/workflows/daily_absen.yml`.

## Catatan Teknis
- Jika UI Maganghub berubah, update selector di `src/infrastructure/automation/selectors.py`.
- Validasi laporan domain memakai minimum panjang karakter terpusat di `src/core/entities.py`.

## Disclaimer
Gunakan alat ini secara bertanggung jawab dan isi laporan sesuai aktivitas nyata.
