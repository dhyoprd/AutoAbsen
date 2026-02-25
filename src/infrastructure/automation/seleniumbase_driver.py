import os
import traceback
from datetime import datetime

from seleniumbase import SB

from src.core.interfaces import IAutomationDriver
from src.core.entities import Report
from .selectors import MagangHubSelectors as Sel

class SeleniumBaseDriver(IAutomationDriver):
    """
    Implementation of IAutomationDriver using SeleniumBase.
    Leverages UC Mode (Undetected Chrome) for bypassing bot detection.
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.sb = None
        self._sb_context = None

        # UC mode can be unstable on some CI runners. Default to non-UC on GitHub Actions,
        # but allow override via env AUTOABSEN_USE_UC=true/false.
        ci_default_uc = os.getenv("GITHUB_ACTIONS", "false").lower() != "true"
        env_uc = os.getenv("AUTOABSEN_USE_UC")
        if env_uc is None:
            self.use_uc = ci_default_uc
        else:
            self.use_uc = env_uc.strip().lower() in {"1", "true", "yes", "on"}

    def _start_session(self) -> bool:
        if self.sb is not None:
            return True

        try:
            self._sb_context = SB(uc=self.use_uc, headless=self.headless, test=True)
            self.sb = self._sb_context.__enter__()
            print(f"-> Browser session started (uc={self.use_uc}, headless={self.headless})")
            return True
        except Exception as e:
            print(f"X Failed to start browser session (uc={self.use_uc}): {e}")
            self.sb = None
            self._sb_context = None

            # Fallback once with non-UC mode for CI stability
            if self.use_uc:
                try:
                    self._sb_context = SB(uc=False, headless=self.headless, test=True)
                    self.sb = self._sb_context.__enter__()
                    self.use_uc = False
                    print("-> Browser session recovered with fallback (uc=False)")
                    return True
                except Exception as fallback_error:
                    print(f"X Fallback browser session also failed: {fallback_error}")
                    self.sb = None
                    self._sb_context = None
            return False

    def _save_debug_artifacts(self, stage: str):
        if not self.sb:
            return

        debug_dir = os.path.join("downloaded_files", "debug")
        os.makedirs(debug_dir, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = f"{stamp}_{stage}"

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
            with open(meta_path, "w", encoding="utf-8") as f:
                f.write(f"url={self.sb.get_current_url()}\n")
                f.write(f"title={self.sb.get_title()}\n")
        except Exception:
            pass

    def execute_full_flow(self, email: str, password: str, report: Report) -> bool:
        """
        Executes the full automation flow in one browser session.
        """
        if not self._start_session():
            return False

        try:
            if not self.login(email, password):
                return False
            if not self.navigate_to_report_page():
                return False
            if not self.fill_report(report):
                return False
            return self.submit_report()
        finally:
            self.close()

    def _login(self, email: str, password: str) -> bool:
        try:
            print("-> Opening Login Page...")
            self.sb.open(Sel.LOGIN_URL)
            self.sb.wait_for_element_visible(Sel.USERNAME_INPUT, timeout=15)
            self.sb.wait_for_element_visible(Sel.PASSWORD_INPUT, timeout=15)
            self.sb.type(Sel.USERNAME_INPUT, email)
            self.sb.type(Sel.PASSWORD_INPUT, password)
            self.sb.click(Sel.LOGIN_BUTTON)

            # Wait for either successful redirect or visible dashboard marker.
            for _ in range(20):
                current_url = (self.sb.get_current_url() or "").lower()

                if "/login" not in current_url and "monev.maganghub.kemnaker.go.id" in current_url:
                    print(f"OK Login redirect detected: {current_url}")
                    return True

                if self.sb.is_element_visible(Sel.DASHBOARD_MARKERS):
                    print("OK Dashboard marker found")
                    return True

                if self.sb.is_element_visible(Sel.LOGIN_ERROR_TEXT):
                    err_text = self.sb.get_text(Sel.LOGIN_ERROR_TEXT)
                    print(f"X Login rejected by server: {err_text}")
                    self._save_debug_artifacts("login_rejected")
                    return False

                self.sb.sleep(1)

            self._save_debug_artifacts("login_timeout")
            print("X Login timeout: dashboard marker not found and URL stayed on login page")
            return False
        except Exception as e:
            print(f"X Login failed: {e}")
            self._save_debug_artifacts("login_exception")
            return False

    def _navigate_to_today(self) -> bool:
        try:
            print("-> Navigating to Today's Report...")
            # Assuming we are on dashboard with calendar
            self.sb.wait_for_element_clickable(Sel.CALENDAR_TODAY_CELL, timeout=10)
            self.sb.click(Sel.CALENDAR_TODAY_CELL)
            
            # Wait for dialog
            self.sb.wait_for_element_visible(Sel.DIALOG_CONTAINER, timeout=5)
            print("OK Report dialog opened")
            return True
        except Exception as e:
            print(f"X Failed to open report dialog: {e}")
            self._save_debug_artifacts("navigate_exception")
            return False

    def _fill_form(self, report: Report) -> bool:
        try:
            print("-> Filling Report Form...")

            self.sb.wait_for_element_visible(Sel.TEXTAREA, timeout=10)
            textareas = self.sb.find_elements(Sel.TEXTAREA)
            visible_textareas = self.sb.driver.execute_script(
                """
                const all = Array.from(document.querySelectorAll('textarea'));
                return all.filter((el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    const visible = rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                    const inActiveOverlay = !!el.closest('.v-overlay--active, .v-dialog--active, [role="dialog"]');
                    return visible && inActiveOverlay;
                });
                """
            )

            if len(visible_textareas) < 3:
                print(f"! Not enough visible textareas found! got={len(visible_textareas)} total={len(textareas)}")
                self._save_debug_artifacts("textareas_not_enough")
                return False

            field_values = [report.activity, report.learning, report.obstacles]
            for index, value in enumerate(field_values):
                area = visible_textareas[index]
                self.sb.driver.execute_script(
                    """
                    arguments[0].focus();
                    arguments[0].value = '';
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].value = arguments[1];
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                    """,
                    area,
                    value,
                )

            # Checkbox must be checked before submit button becomes enabled.
            self.sb.wait_for_element_visible(Sel.CHECKBOX, timeout=10)
            is_checked = self.sb.driver.execute_script(
                "const el=document.querySelector(arguments[0]); return !!(el && el.checked);",
                Sel.CHECKBOX,
            )

            if not is_checked:
                try:
                    self.sb.click(Sel.CONFIRM_CHECKBOX_LABEL)
                except Exception:
                    self.sb.click(Sel.CHECKBOX)

                is_checked = self.sb.driver.execute_script(
                    "const el=document.querySelector(arguments[0]); return !!(el && el.checked);",
                    Sel.CHECKBOX,
                )
                if not is_checked:
                    print("! Confirmation checkbox is still unchecked after click")
                    self._save_debug_artifacts("checkbox_not_checked")
                    return False

            print("OK Form filled")
            return True
        except Exception as e:
            print(f"X Failed to fill form: {e}")
            print(traceback.format_exc())
            self._save_debug_artifacts("fill_exception")
            return False

    def _submit(self) -> bool:
        try:
            print("-> Submitting Report...")
            submit_button = None

            # Wait until candidate submit button is enabled.
            for _ in range(10):
                buttons = self.sb.find_elements("button")
                for button in buttons:
                    button_text = (button.text or "").strip().lower()
                    button_class = (button.get_attribute("class") or "").lower()
                    is_candidate = (
                        "simpan" in button_text
                        or "kirim" in button_text
                        or "submit" in button_text
                        or "bg-black" in button_class
                    )
                    is_disabled = (
                        button.get_attribute("disabled") is not None
                        or "v-btn--disabled" in button_class
                    )
                    if is_candidate and not is_disabled:
                        submit_button = button
                        break

                if submit_button is not None:
                    break
                self.sb.sleep(1)

            if submit_button is None:
                print("! Submit button candidate not found in enabled state")
                self._save_debug_artifacts("submit_button_not_found")
                return False

            try:
                submit_button.click()
            except Exception:
                self.sb.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", submit_button
                )
                self.sb.driver.execute_script("arguments[0].click();", submit_button)

            # Validation: dialog should close after submit.
            for _ in range(10):
                if not self.sb.is_element_visible(Sel.DIALOG_CONTAINER):
                    print("OK Report submitted successfully")
                    return True
                self.sb.sleep(1)

            print("! Dialog still visible, submit might have failed")
            self._save_debug_artifacts("submit_not_closed")
            return False
        except Exception as e:
            print(f"X Failed to submit: {e}")
            self._save_debug_artifacts("submit_exception")
            return False

    def login(self, email: str, password: str) -> bool:
        if not self._start_session():
            return False
        return self._login(email, password)

    def navigate_to_report_page(self) -> bool:
        if not self.sb:
            return False
        return self._navigate_to_today()

    def fill_report(self, report: Report) -> bool:
        if not self.sb:
            return False
        return self._fill_form(report)

    def submit_report(self) -> bool:
        if not self.sb:
            return False
        return self._submit()

    def close(self):
        if self._sb_context is None:
            return
        try:
            self._sb_context.__exit__(None, None, None)
        finally:
            self._sb_context = None
            self.sb = None
