# Deployment Guide

## Mode yang didukung
- `src/workflow_runner.py`: workflow Telegram short-lived (cocok untuk GitHub Actions schedule).
- `src/bot_runner.py`: bot Telegram long-running (cocok untuk VPS/container selalu aktif).

## Opsi 1: GitHub Actions (Scheduled)
Workflow siap pakai ada di `.github/workflows/daily_absen.yml`.

1. Set repository secrets:
`MAGANGHUB_EMAIL`, `MAGANGHUB_PASSWORD`, `OPENROUTER_API_KEY`,
`TELEGRAM_BOT_TOKEN`, `ALLOWED_TELEGRAM_ID`, `AKTIVITAS_KONTEKS`.
2. Sesuaikan cron timezone di `.github/workflows/daily_absen.yml`.
3. Trigger manual via `workflow_dispatch` untuk test awal.

Catatan: runner ini bukan daemon 24/7; dia hanya hidup saat jadwal jalan.

## Opsi 2: VPS/Server Container (Long-running bot)
1. Install Docker + Docker Compose.
2. Copy project + `.env`.
3. Jalankan `docker compose up -d`.
4. Ubah command container jika ingin mode bot long-running:
`python src/bot_runner.py`.

## Opsi 3: Menjalankan langsung di VM
1. `pip install -r requirements.txt`
2. Jalankan:
- `python src/workflow_runner.py` (short-lived interactive workflow), atau
- `python src/bot_runner.py` (long-running).
