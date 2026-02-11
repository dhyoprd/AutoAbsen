# 🚀 AutoAbsen Maganghub - macOS App

Aplikasi macOS untuk otomatisasi pengisian laporan harian di Maganghub dengan bantuan AI.

## 📦 Installation

1. **Clone atau download project ini**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. **Build aplikasi macOS**:
   ```bash
   python3 build_app.py
   ```
   atau jalankan manual:
   ```bash
   python3 -c "
   import PyInstaller.__main__
   PyInstaller.__main__.run([
       'main.py',
       '--onedir',
       '--windowed',
       '--name=AutoAbsen',
       '--add-data=.env:.',
       '--hidden-import=selenium',
       '--hidden-import=webdriver_manager',
       '--hidden-import=colorama',
       '--hidden-import=python-dotenv',
       '--hidden-import=schedule',
       '--hidden-import=requests'
   ])
   "
   ```

## 🎯 Cara Menjalankan

### Opsi 1: Menggunakan Launcher Script
```bash
./run_app.sh
```

### Opsi 2: Jalankan Langsung
```bash
open dist/AutoAbsen.app
```
atau
```bash
./dist/AutoAbsen
```

## ⚙️ Konfigurasi

Pastikan file `.env` sudah dikonfigurasi dengan benar:

```env
# Akun Maganghub
MAGANGHUB_EMAIL=your_email@example.com
MAGANGHUB_PASSWORD=your_password_here

# OpenRouter API Key
OPENROUTER_API_KEY=your_api_key_here

# Konteks aktivitas
AKTIVITAS_KONTEKS=Deskripsikan aktivitas magang Anda

# Jadwal absen (format 24 jam)
JADWAL_ABSEN=16:00

# Mode browser
SHOW_BROWSER=true
```

## 📱 Fitur Aplikasi

- ✅ **AI-Powered Content**: Generate laporan otomatis dengan OpenRouter AI
- ✅ **Automated Browser**: Selenium automation untuk Maganghub
- ✅ **Scheduled Tasks**: Jalankan otomatis sesuai jadwal
- ✅ **User-Friendly**: Interface terminal yang mudah digunakan
- ✅ **Cross-Platform**: Bekerja di macOS, Windows, Linux

## 🛠️ Troubleshooting

### Error: "App cannot be opened because it is from an unidentified developer"
1. Buka **System Settings** > **Privacy & Security**
2. Cari pesan tentang AutoAbsen
3. Klik **"Open Anyway"**

### Error: "ChromeDriver not found"
Aplikasi akan otomatis download ChromeDriver yang diperlukan.

### Error: "API Key not found"
Pastikan file `.env` ada dan berisi OPENROUTER_API_KEY yang valid.

## 📂 Struktur File

```
AutoAbsen/
├── dist/
│   ├── AutoAbsen.app/          # macOS App Bundle
│   └── AutoAbsen               # Standalone executable
├── run_app.sh                  # Launcher script
├── build_app.py               # Build script (opsional)
├── main.py                    # Main application
├── gemini_ai.py              # AI module (OpenRouter)
├── automation.py             # Selenium automation
├── requirements.txt          # Python dependencies
└── .env                      # Configuration file
```

## 🔄 Update Aplikasi

Untuk update aplikasi:

1. Pull/update kode terbaru
2. Install dependencies baru jika ada
3. Jalankan build ulang:
   ```bash
   python3 build_app.py
   ```

## 📞 Support

Jika ada masalah, pastikan:
- Python 3.8+ terinstall
- Google Chrome terinstall
- File `.env` dikonfigurasi dengan benar
- OpenRouter API key valid dan memiliki credit

---

**Happy Automating! 🤖✨**