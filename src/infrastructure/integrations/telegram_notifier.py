from typing import Optional

import requests


class TelegramNotifier:
    """
    Simple Telegram sender via Bot API.
    Keeps dependency isolated from business logic.
    """

    def __init__(self, bot_token: Optional[str], chat_id: Optional[str], timeout_seconds: int = 20):
        self.bot_token = (bot_token or "").strip()
        self.chat_id = (chat_id or "").strip()
        self.timeout_seconds = timeout_seconds

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str) -> bool:
        if not self.is_configured():
            print("⚠️ Telegram notifier is not configured.")
            return False

        endpoint = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            return True
        except Exception as error:
            print(f"⚠️ Failed to send Telegram message: {error}")
            return False
