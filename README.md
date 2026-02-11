# 🤖 AutoAbsen Maganghub + OpenRouter AI

Otomatisasi pengisian laporan harian di [Maganghub Kemnaker](https://monev.maganghub.kemnaker.go.id) dengan bantuan **OpenRouter AI** untuk generate konten.

## ✨ Fitur

- 🤖 **AI-Powered Content** - OpenRouter AI generate uraian aktivitas, pembelajaran, dan kendala
- 🌐 **Auto Fill Form** - Selenium mengisi form laporan harian otomatis
- ⏰ **Scheduler** - Jadwalkan absen otomatis setiap hari
- 🔒 **Secure** - Kredensial disimpan di file .env (tidak di-commit ke git)

## 📋 Persyaratan

- Python 3.8+
- Google Chrome browser
- Akun Maganghub
- API Key OpenRouter

## 🚀 Instalasi

### 1. Clone/Download Project

```bash
cd /path/to/AutoAbsen
```

### 2. Buat Virtual Environment (Opsional tapi Recommended)

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# atau
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment

```bash
# Copy file contoh
cp .env.example .env

# Edit file .env dengan text editor
nano .env  # atau buka dengan VS Code
```

Isi konfigurasi berikut:

```env
# Akun Maganghub
MAGANGHUB_EMAIL=email_kamu@example.com
MAGANGHUB_PASSWORD=password_kamu

# OpenRouter API Key (dapatkan di https://openrouter.ai/keys)
OPENROUTER_API_KEY=your_api_key_here

# Konteks aktivitas magang (untuk AI)
AKTIVITAS_KONTEKS=Saya mahasiswa magang di bidang IT, aktivitas meliputi coding, meeting, dll

# Jadwal (format 24 jam)
JADWAL_ABSEN=08:00

# Mode browser (true/false)
SHOW_BROWSER=true
```

### 5. Dapatkan OpenRouter API Key

1. Buka [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Login dengan akun Google
3. Klik "Create API Key"
4. Copy API key dan paste ke file `.env`

## 📖 Cara Penggunaan

### Mode Manual (Recommended untuk pertama kali)

```bash
python main.py
```

Langkah-langkah:
1. Program akan bertanya "Apa yang kamu lakukan hari ini?"
2. Jawab singkat aktivitasmu (contoh: "belajar python, meeting mentor")
3. AI akan generate konten lengkap
4. Review konten yang di-generate
5. Konfirmasi untuk lanjut ke pengisian form
6. Browser terbuka dan form diisi otomatis
7. Review dan klik "Simpan dan Kirim" manual

### Mode Scheduler (Auto harian)

```bash
python scheduler.py
```

Program akan berjalan terus dan otomatis absen sesuai jadwal di `.env`.

## 📁 Struktur Project

```
AutoAbsen/
├── main.py           # Script utama
├── gemini_ai.py      # Module OpenRouter AI
├── automation.py     # Module Selenium automation
├── scheduler.py      # Scheduler untuk auto harian
├── requirements.txt  # Dependencies
├── .env.example      # Contoh konfigurasi
├── .env              # Konfigurasi (buat sendiri)
└── README.md         # Dokumentasi ini
```

## ⚠️ Catatan Penting

1. **Selector HTML** - Jika website Maganghub berubah, selector di `automation.py` mungkin perlu diupdate
2. **Auto Submit** - Secara default, submit TIDAK otomatis. Uncomment baris `submit_laporan()` di `automation.py` jika ingin full auto
3. **Captcha** - Jika ada captcha, perlu intervensi manual
4. **Rate Limit** - OpenRouter API memiliki rate limit, jangan spam request

## 🔧 Troubleshooting

### Browser tidak terbuka
```bash
# Install Chrome WebDriver manual jika perlu
pip install webdriver-manager --upgrade
```

### Login gagal
- Pastikan email dan password benar
- Cek apakah ada 2FA/OTP
- Coba login manual dulu untuk verifikasi

### OpenRouter error
- Cek API key valid
- Pastikan quota API belum habis
- Cek koneksi internet

### Selector tidak ditemukan
Website mungkin update, perlu inspect element dan update selector di `automation.py`.

## 📜 Disclaimer

Tools ini dibuat untuk tujuan edukasi dan memudahkan proses absensi. Gunakan dengan bijak dan tetap isi laporan dengan jujur sesuai aktivitas yang benar-benar dilakukan.

## 📝 License

MIT License - bebas digunakan dan dimodifikasi.

---

Made by @dhyoprd
