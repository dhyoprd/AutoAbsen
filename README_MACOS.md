# AutoAbsen di macOS

Dokumen ini khusus catatan eksekusi di macOS. Referensi utama tetap `README.md`.

## Setup Cepat
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Jalankan
CLI manual:
```bash
python src/main.py
```

Telegram bot long-running:
```bash
python src/bot_runner.py
```

Workflow short-lived:
```bash
python src/workflow_runner.py
```

## Troubleshooting macOS
- Jika browser automation gagal, pastikan Chrome/Chromium terpasang.
- Jika muncul kendala izin saat compile bytecode, gunakan:
`PYTHONPYCACHEPREFIX=.pycache_tmp`.
