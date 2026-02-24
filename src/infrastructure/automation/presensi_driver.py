import os
import time
from datetime import datetime
from typing import Tuple
from urllib.parse import urlparse

from selenium.common.exceptions import NoAlertPresentException
from seleniumbase import SB

from .presensi_selectors import PresensiSelectors as Sel


class PresensiDriver:
    """
    Browser automation driver for external attendance page.
    Keeps SRP: only handles browser interactions.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.sb = None
        self._sb_context = None

    def _start_session(self) -> bool:
        if self.sb is not None:
            return True

        try:
            self._sb_context = SB(uc=True, headless=self.headless, test=True)
            self.sb = self._sb_context.__enter__()
            return True
        except Exception as error:
            print(f"❌ Failed to start browser session: {error}")
            self.sb = None
            self._sb_context = None
            return False

    def _save_debug_artifacts(self, stage: str):
        if not self.sb:
            return

        debug_dir = os.path.join("downloaded_files", "debug")
        os.makedirs(debug_dir, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = f"{stamp}_presensi_{stage}"

        try:
            self.sb.save_screenshot(f"{base_name}.png", folder=debug_dir)
        except Exception:
            pass

        try:
            self.sb.save_page_source(f"{base_name}.html", folder=debug_dir)
        except Exception:
            pass

        try:
            meta_path = os.path.join(debug_dir, f"{base_name}.txt")
            with open(meta_path, "w", encoding="utf-8") as file:
                file.write(f"url={self.sb.get_current_url()}\n")
                file.write(f"title={self.sb.get_title()}\n")
        except Exception:
            pass

    def _is_google_login_redirect(self) -> bool:
        if not self.sb:
            return False

        try:
            current_url = (self.sb.get_current_url() or "").lower()
            host = (urlparse(current_url).hostname or "").lower()
            return "accounts.google.com" in host or "signin" in current_url
        except Exception:
            return False

    def _consume_alert_text(self) -> str:
        if not self.sb:
            return ""

        try:
            alert = self.sb.driver.switch_to.alert
            text = (alert.text or "").strip()
            alert.accept()
            return text
        except NoAlertPresentException:
            return ""
        except Exception:
            return ""

    def _wait_feedback(self, timeout_seconds: int = 10) -> Tuple[bool, str]:
        if not self.sb:
            return False, "Browser session is not available."

        success_keywords = ("berhasil", "sukses", "success")
        failure_keywords = ("gagal", "failed", "error")
        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            alert_text = self._consume_alert_text()
            if alert_text:
                lowered = alert_text.lower()
                if any(word in lowered for word in failure_keywords):
                    return False, f"Alert: {alert_text}"
                if any(word in lowered for word in success_keywords):
                    return True, f"Alert: {alert_text}"
                return True, f"Alert: {alert_text}"

            page_text = ""
            try:
                page_text = (self.sb.get_text("body") or "").lower()
            except Exception:
                page_text = ""

            if any(word in page_text for word in failure_keywords):
                return False, "Failure message detected on page."
            if any(word in page_text for word in success_keywords):
                return True, "Success message detected on page."

            self.sb.sleep(1)

        return True, "Button clicked, no explicit confirmation text found."

    def submit_presensi(
        self,
        url: str,
        full_name: str,
        unit_name: str,
        action: str,
    ) -> Tuple[bool, str]:
        normalized_action = action.strip().upper()
        button_selector = Sel.ACTION_BUTTONS.get(normalized_action)
        if not button_selector:
            return False, f"Unsupported action: {action}"

        if not self._start_session():
            return False, "Failed to initialize browser session."

        try:
            print("-> Opening external presensi page...")
            self.sb.open(url)
            self.sb.sleep(2)

            if self._is_google_login_redirect():
                self._save_debug_artifacts("auth_redirect")
                return False, "Auth redirect detected (Google sign-in required). Endpoint is not CI-accessible."

            self.sb.wait_for_element_visible(Sel.NAME_INPUT, timeout=20)
            self.sb.wait_for_element_visible(Sel.UNIT_SELECT, timeout=20)

            print("-> Filling name and unit...")
            self.sb.clear(Sel.NAME_INPUT)
            self.sb.type(Sel.NAME_INPUT, full_name)
            self.sb.select_option_by_text(Sel.UNIT_SELECT, unit_name)

            print(f"-> Clicking button for action: {normalized_action}...")
            self.sb.wait_for_element_clickable(button_selector, timeout=20)
            self.sb.click(button_selector)

            success, message = self._wait_feedback(timeout_seconds=10)
            if success:
                print(f"✅ Presensi {normalized_action} succeeded. {message}")
                return True, message

            self._save_debug_artifacts("submission_failed")
            print(f"❌ Presensi {normalized_action} failed. {message}")
            return False, message
        except Exception as error:
            if self._is_google_login_redirect():
                self._save_debug_artifacts("auth_redirect_exception")
                return False, "Auth redirect detected while waiting form fields (Google sign-in required)."

            self._save_debug_artifacts("exception")
            return False, f"Automation exception: {error}"
        finally:
            self.close()

    def close(self):
        if self._sb_context is None:
            return
        try:
            self._sb_context.__exit__(None, None, None)
        finally:
            self._sb_context = None
            self.sb = None
