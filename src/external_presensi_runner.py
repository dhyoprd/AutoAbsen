import os
import sys
from datetime import datetime, timedelta, timezone

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.automation.presensi_driver import PresensiDriver
from src.infrastructure.integrations.telegram_notifier import TelegramNotifier


DEFAULT_PRESENSI_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbz5M9sws7DUOiTWCt3vyCgUiMsXkTN-M72sjC4hdyyMGGyHVKm99d-gmwemYQVA7Q0f/exec"
)
DEFAULT_FULL_NAME = "Made Dhyo Pradnyadiva"
DEFAULT_UNIT = "Pengembangan Aplikasi"


def _parse_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _build_notification_message(
    success: bool,
    action: str,
    full_name: str,
    unit_name: str,
    details: str,
) -> str:
    wita = timezone(timedelta(hours=8))
    now_wita = datetime.now(wita).strftime("%Y-%m-%d %H:%M:%S WITA")
    status_icon = "✅" if success else "❌"
    status_text = "BERHASIL" if success else "GAGAL"
    return (
        f"{status_icon} Presensi {action} {status_text}\n"
        f"Waktu: {now_wita}\n"
        f"Nama: {full_name}\n"
        f"Unit: {unit_name}\n"
        f"Detail: {details}"
    )


def run() -> bool:
    enabled = _parse_bool(os.getenv("PRESENSI_ENABLED"), True)
    if not enabled:
        print("⏭ PRESENSI_ENABLED=false, skipping external presensi execution.")
        return True

    url = (os.getenv("PRESENSI_URL") or DEFAULT_PRESENSI_URL).strip()
    full_name = (os.getenv("PRESENSI_FULL_NAME") or DEFAULT_FULL_NAME).strip()
    unit_name = (os.getenv("PRESENSI_UNIT") or DEFAULT_UNIT).strip()
    action = (os.getenv("PRESENSI_ACTION") or "").strip().upper()
    show_browser = _parse_bool(os.getenv("PRESENSI_SHOW_BROWSER"), False)

    if not url:
        print("❌ PRESENSI_URL is empty.")
        return False
    if not full_name:
        print("❌ PRESENSI_FULL_NAME is empty.")
        return False
    if not unit_name:
        print("❌ PRESENSI_UNIT is empty.")
        return False
    if action not in {"MASUK", "KELUAR"}:
        print("❌ PRESENSI_ACTION must be either MASUK or KELUAR.")
        return False

    driver = PresensiDriver(headless=not show_browser)
    success, details = driver.submit_presensi(
        url=url,
        full_name=full_name,
        unit_name=unit_name,
        action=action,
    )

    notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("ALLOWED_TELEGRAM_ID"),
    )
    notification_message = _build_notification_message(
        success=success,
        action=action,
        full_name=full_name,
        unit_name=unit_name,
        details=details,
    )
    notif_sent = notifier.send_message(notification_message)

    if not notif_sent:
        print("❌ Notification failed to send to Telegram.")
        return False

    return success


def main():
    ok = run()
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
