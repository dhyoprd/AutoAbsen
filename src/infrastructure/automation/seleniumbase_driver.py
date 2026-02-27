import os
import traceback
from datetime import datetime

from seleniumbase import SB
from selenium.webdriver.common.keys import Keys

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

    def _log(self, code: str, message: str):
        print(f"[{code}] {message}")

    def _start_session(self) -> bool:
        if self.sb is not None:
            return True

        try:
            self._sb_context = SB(uc=self.use_uc, headless=self.headless, test=True)
            self.sb = self._sb_context.__enter__()
            self._log(
                "MH-DRIVER-START-OK",
                f"Browser session started (uc={self.use_uc}, headless={self.headless})",
            )
            return True
        except Exception as e:
            self._log(
                "MH-DRIVER-START-ERR",
                f"Failed to start browser session (uc={self.use_uc}): {e}",
            )
            self.sb = None
            self._sb_context = None

            # Fallback once with non-UC mode for CI stability
            if self.use_uc:
                try:
                    self._sb_context = SB(uc=False, headless=self.headless, test=True)
                    self.sb = self._sb_context.__enter__()
                    self.use_uc = False
                    self._log(
                        "MH-DRIVER-START-FALLBACK-OK",
                        "Browser session recovered with fallback (uc=False)",
                    )
                    return True
                except Exception as fallback_error:
                    self._log(
                        "MH-DRIVER-START-FALLBACK-ERR",
                        f"Fallback browser session also failed: {fallback_error}",
                    )
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

    def _get_confirm_checkbox_state(self) -> dict:
        if not self.sb:
            return {"found": False, "checked": False, "forId": "", "source": "no-session"}

        try:
            state = self.sb.driver.execute_script(
                """
                const dialog = document.querySelector('.v-dialog--active, .v-overlay--active, [role="dialog"]') || document;
                const normalize = (text) => (text || '').toLowerCase().replace(/\\s+/g, ' ').trim();
                const keywords = ['meninjau', 'isian laporan ini sudah benar', 'laporan ini sudah benar'];

                const labels = Array.from(dialog.querySelectorAll('label'));
                for (const label of labels) {
                    const labelText = normalize(label.textContent);
                    if (!keywords.some((key) => labelText.includes(key))) continue;

                    const forId = label.getAttribute('for') || '';
                    if (forId) {
                        let byId = null;
                        try {
                            const escaped = (window.CSS && CSS.escape) ? CSS.escape(forId) : forId;
                            byId = dialog.querySelector(`#${escaped}`);
                        } catch (e) {}
                        if (!byId) {
                            const byDoc = document.getElementById(forId);
                            if (byDoc && dialog.contains(byDoc)) {
                                byId = byDoc;
                            }
                        }
                        if (byId && byId.type === 'checkbox') {
                            return {found: true, checked: !!byId.checked, forId, source: 'label-for'};
                        }
                    }

                    const parent = label.parentElement || dialog;
                    const nested = parent.querySelector('input[type="checkbox"]');
                    if (nested) {
                        return {
                            found: true,
                            checked: !!nested.checked,
                            forId: nested.id || '',
                            source: 'label-parent',
                        };
                    }
                }

                const checkboxes = Array.from(dialog.querySelectorAll('input[type="checkbox"]'));
                if (checkboxes.length === 1) {
                    return {
                        found: true,
                        checked: !!checkboxes[0].checked,
                        forId: checkboxes[0].id || '',
                        source: 'single-fallback',
                    };
                }

                return {found: false, checked: false, forId: '', source: 'not-found'};
                """
            )
            if not isinstance(state, dict):
                return {"found": False, "checked": False, "forId": "", "source": "invalid-response"}
            return state
        except Exception:
            return {"found": False, "checked": False, "forId": "", "source": "js-exception"}

    def _try_check_confirm_checkbox(self) -> bool:
        if not self.sb:
            return False

        try:
            result = self.sb.driver.execute_script(
                """
                const dialog = document.querySelector('.v-dialog--active, .v-overlay--active, [role="dialog"]') || document;
                const normalize = (text) => (text || '').toLowerCase().replace(/\\s+/g, ' ').trim();
                const labels = Array.from(dialog.querySelectorAll('label'));
                const targetLabel = labels.find((label) => {
                    const value = normalize(label.textContent);
                    return value.includes('meninjau') || value.includes('laporan ini sudah benar');
                });

                let input = null;
                if (targetLabel) {
                    const forId = targetLabel.getAttribute('for');
                    if (forId) {
                        try {
                            const escaped = (window.CSS && CSS.escape) ? CSS.escape(forId) : forId;
                            input = dialog.querySelector(`#${escaped}`);
                        } catch (e) {}
                        if (!input) {
                            const byDoc = document.getElementById(forId);
                            if (byDoc && dialog.contains(byDoc)) {
                                input = byDoc;
                            }
                        }
                    }
                    if (!input) {
                        input = (targetLabel.parentElement || dialog).querySelector('input[type="checkbox"]');
                    }
                }
                if (!input) {
                    const all = Array.from(dialog.querySelectorAll('input[type="checkbox"]'));
                    if (all.length === 1) {
                        input = all[0];
                    }
                }
                if (!input) return false;

                const wrapper =
                    input.closest('.v-selection-control')?.querySelector('.v-selection-control__wrapper') ||
                    input.closest('.v-input')?.querySelector('.v-selection-control__wrapper');
                const clickTargets = [targetLabel, wrapper, input].filter(Boolean);

                for (const target of clickTargets) {
                    if (input.checked) break;
                    target.click();
                }
                if (!input.checked) {
                    input.checked = true;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }

                return !!input.checked;
                """
            )
            if result:
                state = self._get_confirm_checkbox_state()
                if state.get("checked"):
                    self._log("MH-FILL-CHECKBOX-OK", f"Checkbox checked via active-dialog JS strategy ({state.get('source')}).")
                    return True
        except Exception:
            pass

        label_strategies = [
            Sel.CONFIRM_CHECKBOX_LABEL,
            "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'meninjau')]",
            "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'laporan')]",
        ]
        for selector in label_strategies:
            try:
                self.sb.click(selector)
            except Exception:
                continue

            state = self._get_confirm_checkbox_state()
            if state.get("checked"):
                self._log("MH-FILL-CHECKBOX-OK", f"Checkbox checked via selector strategy ({state.get('source')}).")
                return True

        state = self._get_confirm_checkbox_state()
        if state.get("checked"):
            self._log("MH-FILL-CHECKBOX-OK", f"Checkbox checked via JS strategy ({state.get('source')}).")
            return True
        return False

    def _get_visible_report_textareas(self) -> list:
        if not self.sb:
            return []
        try:
            return self.sb.driver.execute_script(
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
            ) or []
        except Exception:
            return []

    def _fill_single_textarea_send_keys(self, area, value: str):
        try:
            self.sb.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", area)
        except Exception:
            pass
        try:
            area.click()
        except Exception:
            pass
        try:
            area.send_keys(Keys.CONTROL, "a")
            area.send_keys(Keys.BACKSPACE)
        except Exception:
            try:
                area.clear()
            except Exception:
                pass
        area.send_keys(value)
        try:
            area.send_keys(Keys.TAB)
        except Exception:
            pass

    def _fill_single_textarea_js(self, area, value: str):
        self.sb.driver.execute_script(
            """
            arguments[0].focus();
            arguments[0].value = '';
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
            """,
            area,
            value,
        )

    def _fill_report_fields_robust(self, values: list) -> list:
        """Fill activity/learning/obstacles one-by-one with fresh element lookup."""
        methods = ("send_keys", "js", "send_keys")
        final_lengths = [0, 0, 0]

        for index, value in enumerate(values):
            field_filled = False
            for method in methods:
                textareas = self._get_visible_report_textareas()
                if len(textareas) < 3:
                    break

                area = textareas[index]
                try:
                    if method == "send_keys":
                        self._fill_single_textarea_send_keys(area, value)
                    else:
                        self._fill_single_textarea_js(area, value)
                except Exception:
                    continue

                self._blur_textareas([area])
                self.sb.sleep(0.5)

                current_textareas = self._get_visible_report_textareas()
                if len(current_textareas) < 3:
                    continue

                current_len = self._get_textarea_lengths([current_textareas[index]])[0]
                final_lengths[index] = current_len
                self._log(
                    "MH-FILL-FIELD-LEN",
                    f"Field index={index} length after {method}: {current_len}",
                )
                if current_len >= 100:
                    field_filled = True
                    break

            if not field_filled:
                return final_lengths
        return final_lengths

    def _get_textarea_lengths(self, textareas: list) -> list:
        return self.sb.driver.execute_script(
            """
            return arguments[0].map((el) => ((el.value || '').trim().length));
            """,
            textareas,
        )

    def _blur_textareas(self, textareas: list):
        try:
            self.sb.driver.execute_script(
                """
                arguments[0].forEach((el) => {
                    try {
                        el.blur();
                        el.dispatchEvent(new Event('blur', { bubbles: true }));
                    } catch (e) {}
                });
                """,
                textareas,
            )
        except Exception:
            pass

    def _get_submit_candidate_states(self) -> list:
        if not self.sb:
            return []
        try:
            states = self.sb.driver.execute_script(
                """
                const dialog = document.querySelector('.v-dialog--active, .v-overlay--active, [role="dialog"]') || document;
                const buttons = Array.from(dialog.querySelectorAll('button'));
                return buttons
                    .map((button) => {
                        const text = ((button.textContent || '').trim().toLowerCase());
                        const className = ((button.getAttribute('class') || '').toLowerCase());
                        const isCandidate = text.includes('simpan') || text.includes('kirim') || text.includes('submit') || className.includes('bg-black');
                        if (!isCandidate) return null;
                        const disabled = button.hasAttribute('disabled') || className.includes('v-btn--disabled');
                        return {text: text.slice(0, 60), disabled, class: className.slice(0, 120)};
                    })
                    .filter(Boolean);
                """
            )
            return states if isinstance(states, list) else []
        except Exception:
            return []

    def _find_enabled_submit_button(self, attempts: int = 10, sleep_seconds: int = 1, log_wait: bool = True):
        submit_button = None
        for attempt in range(attempts):
            buttons = self.sb.driver.execute_script(
                """
                const dialog = document.querySelector('.v-dialog--active, .v-overlay--active, [role="dialog"]') || document;
                return Array.from(dialog.querySelectorAll('button'));
                """
            ) or []
            candidate_states = []

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
                if is_candidate:
                    candidate_states.append(
                        {
                            "text": button_text[:60],
                            "disabled": is_disabled,
                            "class": button_class[:120],
                        }
                    )
                if is_candidate and not is_disabled:
                    submit_button = button
                    break

            if submit_button is not None:
                return submit_button

            if log_wait:
                if candidate_states:
                    self._log(
                        "MH-SUBMIT-WAIT",
                        f"Attempt {attempt + 1}: submit candidate(s) exist but still disabled: {candidate_states}",
                    )
                else:
                    self._log(
                        "MH-SUBMIT-WAIT",
                        f"Attempt {attempt + 1}: no submit candidate found in active dialog",
                    )
            self.sb.sleep(sleep_seconds)

        return None

    def _get_report_dialog_state(self) -> dict:
        if not self.sb:
            return {"open": False, "visibleDialogs": 0, "reportDialogs": 0, "source": "no-session"}
        try:
            state = self.sb.driver.execute_script(
                """
                const normalize = (text) => (text || '').toLowerCase().replace(/\\s+/g, ' ').trim();
                const nodes = Array.from(document.querySelectorAll('.v-dialog--active, .v-overlay--active, [role="dialog"]'));
                const visible = nodes.filter((el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                });
                const reportDialogs = visible.filter((el) => {
                    const text = normalize(el.textContent);
                    const hasTextarea = !!el.querySelector('textarea');
                    return (
                        hasTextarea ||
                        text.includes('tambah laporan harian') ||
                        text.includes('uraian aktivitas') ||
                        text.includes('simpan dan kirim')
                    );
                });
                return {
                    open: reportDialogs.length > 0,
                    visibleDialogs: visible.length,
                    reportDialogs: reportDialogs.length,
                    source: 'active-dialog-scan',
                };
                """
            )
            if isinstance(state, dict):
                return state
        except Exception:
            pass
        return {"open": False, "visibleDialogs": 0, "reportDialogs": 0, "source": "scan-fallback"}

    def _get_submit_feedback(self) -> dict:
        if not self.sb:
            return {
                "errors": [],
                "invalidHints": [],
                "submitButtons": [],
                "checkboxChecked": None,
                "attendanceValue": "",
                "source": "no-session",
            }
        try:
            feedback = self.sb.driver.execute_script(
                """
                const normalize = (text) => (text || '').replace(/\\s+/g, ' ').trim();
                const lower = (text) => normalize(text).toLowerCase();
                const dialogs = Array.from(document.querySelectorAll('.v-dialog--active, .v-overlay--active, [role="dialog"]'));
                const visible = dialogs.filter((el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                });
                const dialog = visible.find((el) => {
                    const text = lower(el.textContent);
                    return (
                        !!el.querySelector('textarea') ||
                        text.includes('tambah laporan harian') ||
                        text.includes('uraian aktivitas') ||
                        text.includes('simpan dan kirim')
                    );
                }) || visible[0] || document;

                const errSelectors = [
                    '.v-messages__message',
                    '.error--text',
                    '.text-danger',
                    '.invalid-feedback',
                    '.v-alert__content',
                    '[role="alert"]',
                ];
                const errors = [];
                errSelectors.forEach((selector) => {
                    dialog.querySelectorAll(selector).forEach((node) => {
                        const text = normalize(node.textContent);
                        if (text) errors.push(text);
                    });
                });
                const invalidHints = [];
                dialog.querySelectorAll('.v-input--error, [aria-invalid="true"], [aria-invalid=true]').forEach((node) => {
                    const text = normalize(node.textContent);
                    if (text) invalidHints.push(text);
                    const label =
                        node.getAttribute('aria-label') ||
                        (node.closest('.v-input')?.querySelector('label, .v-label')?.textContent || '');
                    if (label) invalidHints.push(`invalid: ${normalize(label)}`);
                });

                const buttons = Array.from(dialog.querySelectorAll('button'));
                const submitButtons = buttons
                    .map((button) => {
                        const text = lower(button.textContent);
                        const cls = lower(button.getAttribute('class') || '');
                        const isCandidate = text.includes('simpan') || text.includes('kirim') || text.includes('submit') || cls.includes('bg-black');
                        if (!isCandidate) return null;
                        const disabled = button.hasAttribute('disabled') || cls.includes('v-btn--disabled');
                        return { text: text.slice(0, 60), disabled, class: cls.slice(0, 120) };
                    })
                    .filter(Boolean);

                let checkboxChecked = null;
                const labels = Array.from(dialog.querySelectorAll('label'));
                const targetLabel = labels.find((label) => {
                    const text = lower(label.textContent);
                    return text.includes('meninjau') || text.includes('laporan ini sudah benar');
                });
                if (targetLabel) {
                    const forId = targetLabel.getAttribute('for');
                    let input = null;
                    if (forId) {
                        try {
                            const escaped = (window.CSS && CSS.escape) ? CSS.escape(forId) : forId;
                            input = dialog.querySelector(`#${escaped}`);
                        } catch (e) {}
                        if (!input) {
                            const byDoc = document.getElementById(forId);
                            if (byDoc && dialog.contains(byDoc)) input = byDoc;
                        }
                    }
                    if (!input) {
                        input = (targetLabel.parentElement || dialog).querySelector('input[type="checkbox"]');
                    }
                    if (input) checkboxChecked = !!input.checked;
                }

                let attendanceValue = '';
                const attendanceLabels = Array.from(dialog.querySelectorAll('label, .v-label'));
                const attendanceLabel = attendanceLabels.find((label) => lower(label.textContent).includes('kehadiran'));
                if (attendanceLabel) {
                    const root = attendanceLabel.closest('.v-input') || attendanceLabel.parentElement || dialog;
                    const field =
                        root.querySelector('input, select, .v-select__selection-text, .v-select__selection, .v-field__input') ||
                        root;
                    attendanceValue = normalize(field.value || field.textContent || '');
                }

                return {
                    errors: Array.from(new Set(errors)).slice(0, 5),
                    invalidHints: Array.from(new Set(invalidHints)).slice(0, 6),
                    submitButtons,
                    checkboxChecked,
                    attendanceValue,
                    source: 'dialog-feedback',
                };
                """
            )
            if isinstance(feedback, dict):
                return feedback
        except Exception:
            pass
        return {
            "errors": [],
            "invalidHints": [],
            "submitButtons": [],
            "checkboxChecked": None,
            "attendanceValue": "",
            "source": "feedback-fallback",
        }

    def _ensure_attendance_hadir(self) -> bool:
        if not self.sb:
            return False
        try:
            native = self.sb.driver.execute_script(
                """
                const dialog = document.querySelector('.v-dialog--active, .v-overlay--active, [role="dialog"]') || document;
                const normalize = (text) => (text || '').toLowerCase().replace(/\\s+/g, ' ').trim();
                const select = dialog.querySelector('select');
                if (!select) return {handled: false, selected: false, source: 'no-native-select', value: ''};

                const options = Array.from(select.options || []);
                const target = options.find((opt) => normalize(opt.textContent).includes('hadir'));
                if (!target) return {handled: true, selected: false, source: 'native-select-no-hadir', value: ''};

                select.value = target.value;
                if (select.value !== target.value) {
                    target.selected = true;
                }
                select.dispatchEvent(new Event('input', { bubbles: true }));
                select.dispatchEvent(new Event('change', { bubbles: true }));

                const chosen = options[select.selectedIndex] ? normalize(options[select.selectedIndex].textContent) : '';
                return {handled: true, selected: chosen.includes('hadir'), source: 'native-select', value: chosen};
                """
            )
            if isinstance(native, dict) and native.get("handled"):
                self._log(
                    "MH-FILL-ATTENDANCE",
                    f"Attendance native select result: selected={native.get('selected')}, value={native.get('value')}",
                )
                return bool(native.get("selected"))
        except Exception:
            pass

        try:
            opened = self.sb.driver.execute_script(
                """
                const dialog = document.querySelector('.v-dialog--active, .v-overlay--active, [role="dialog"]') || document;
                const normalize = (text) => (text || '').toLowerCase().replace(/\\s+/g, ' ').trim();
                const labels = Array.from(dialog.querySelectorAll('label, .v-label'));
                const attendanceLabel = labels.find((el) => normalize(el.textContent).includes('kehadiran'));

                let container = null;
                if (attendanceLabel) {
                    container =
                        attendanceLabel.closest('.v-input') ||
                        (attendanceLabel.parentElement || dialog).querySelector('.v-input, .v-select, [role="combobox"], .v-field');
                }
                if (!container) {
                    container = Array.from(dialog.querySelectorAll('.v-input, .v-select, [role="combobox"], .v-field'))
                        .find((el) => normalize(el.textContent).includes('kehadiran'));
                }
                if (!container) return false;

                const target = container.querySelector('[role="combobox"], .v-field__input, .v-input__control, .v-field') || container;
                target.scrollIntoView({ block: 'center' });
                ['mousedown', 'mouseup', 'click'].forEach((name) => {
                    target.dispatchEvent(new MouseEvent(name, { bubbles: true, cancelable: true, view: window }));
                });
                return true;
                """
            )
            if opened:
                option_selectors = [
                    "//div[contains(@class,'v-overlay--active')]//div[contains(@class,'v-list-item-title') and normalize-space()='Hadir']",
                    "//div[contains(@class,'v-overlay--active')]//*[@role='option'][contains(normalize-space(.), 'Hadir')]",
                    "//div[contains(@class,'v-list-item')][contains(normalize-space(.), 'Hadir')]",
                ]
                for option_selector in option_selectors:
                    try:
                        self.sb.wait_for_element_visible(option_selector, timeout=2)
                        self.sb.click(option_selector)
                        break
                    except Exception:
                        continue
        except Exception:
            pass

        try:
            verify = self.sb.driver.execute_script(
                """
                const dialog = document.querySelector('.v-dialog--active, .v-overlay--active, [role="dialog"]') || document;
                const normalize = (text) => (text || '').toLowerCase().replace(/\\s+/g, ' ').trim();
                const blocks = Array.from(dialog.querySelectorAll('.v-input, .v-select, [role="combobox"], .v-field, label, .v-label'));
                const attendanceBlock = blocks.find((el) => normalize(el.textContent).includes('kehadiran'));
                if (!attendanceBlock) return {selected: false, value: '', source: 'verify-not-found'};

                const root = attendanceBlock.closest('.v-input') || attendanceBlock.parentElement || attendanceBlock;
                const typed = root.querySelector('input');
                const display =
                    root.querySelector('.v-select__selection-text, .v-select__selection, .v-field__input') ||
                    typed ||
                    root;
                const raw = typed && typed.value ? typed.value : (display.textContent || '');
                const value = normalize(raw);
                return {selected: value.includes('hadir'), value, source: 'verify-vuetify'};
                """
            )
            if isinstance(verify, dict):
                self._log(
                    "MH-FILL-ATTENDANCE",
                    f"Attendance verify result: selected={verify.get('selected')}, value={verify.get('value')}, source={verify.get('source')}",
                )
                return bool(verify.get("selected"))
        except Exception:
            pass
        return False

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
            self._log("MH-LOGIN-START", "Opening login page")
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
                    self._log("MH-LOGIN-OK-REDIRECT", f"Login redirect detected: {current_url}")
                    return True

                if self.sb.is_element_visible(Sel.DASHBOARD_MARKERS):
                    self._log("MH-LOGIN-OK-MARKER", "Dashboard marker found")
                    return True

                if self.sb.is_element_visible(Sel.LOGIN_ERROR_TEXT):
                    err_text = self.sb.get_text(Sel.LOGIN_ERROR_TEXT)
                    self._log("MH-LOGIN-ERR-REJECTED", f"Login rejected by server: {err_text}")
                    self._save_debug_artifacts("login_rejected")
                    return False

                self.sb.sleep(1)

            self._save_debug_artifacts("login_timeout")
            self._log(
                "MH-LOGIN-ERR-TIMEOUT",
                "Login timeout: dashboard marker not found and URL stayed on login page",
            )
            return False
        except Exception as e:
            self._log("MH-LOGIN-ERR-EXCEPTION", f"Login failed: {e}")
            self._save_debug_artifacts("login_exception")
            return False

    def _navigate_to_today(self) -> bool:
        try:
            self._log("MH-NAV-START", "Navigating to today's report dialog")
            # Assuming we are on dashboard with calendar
            self.sb.wait_for_element_clickable(Sel.CALENDAR_TODAY_CELL, timeout=10)
            self.sb.click(Sel.CALENDAR_TODAY_CELL)
            
            # Wait for dialog
            self.sb.wait_for_element_visible(Sel.DIALOG_CONTAINER, timeout=5)
            self._log("MH-NAV-OK", "Report dialog opened")
            return True
        except Exception as e:
            self._log("MH-NAV-ERR", f"Failed to open report dialog: {e}")
            self._save_debug_artifacts("navigate_exception")
            return False

    def _fill_form(self, report: Report) -> bool:
        try:
            self._log("MH-FILL-START", "Filling report form")

            self.sb.wait_for_element_visible(Sel.TEXTAREA, timeout=10)
            textareas = self.sb.find_elements(Sel.TEXTAREA)
            visible_textareas = self._get_visible_report_textareas()

            if len(visible_textareas) < 3:
                self._log(
                    "MH-FILL-ERR-TEXTAREA",
                    f"Not enough visible textareas found (got={len(visible_textareas)}, total={len(textareas)})",
                )
                self._save_debug_artifacts("textareas_not_enough")
                return False

            field_values = [report.activity, report.learning, report.obstacles]
            filled_lengths = self._fill_report_fields_robust(field_values)
            self._log("MH-FILL-LEN", f"Field lengths after fill: {filled_lengths}")
            if any(length < 100 for length in filled_lengths):
                self._log("MH-FILL-LEN-RETRY", "Retrying robust field fill once more")
                filled_lengths = self._fill_report_fields_robust(field_values)
                self._log("MH-FILL-LEN", f"Field lengths after fallback fill: {filled_lengths}")
                if any(length < 100 for length in filled_lengths):
                    self._log("MH-FILL-ERR-LEN", f"One or more field lengths are still below 100 chars: {filled_lengths}")
                    self._save_debug_artifacts("fill_length_invalid")
                    return False

            attendance_ok = self._ensure_attendance_hadir()
            if attendance_ok:
                self._log("MH-FILL-ATTENDANCE-OK", "Attendance field confirmed as 'Hadir'")
            else:
                self._log("MH-FILL-ATTENDANCE-WARN", "Could not confirm attendance='Hadir' during fill phase")

            # Checkbox can be hidden in Vuetify; try label click first, then fallback to input.
            checkbox_state = self._get_confirm_checkbox_state()
            self._log(
                "MH-FILL-CHECKBOX-STATE",
                f"Confirm checkbox state before click: found={checkbox_state.get('found')}, "
                f"checked={checkbox_state.get('checked')}, source={checkbox_state.get('source')}",
            )
            if not checkbox_state.get("checked"):
                checked = self._try_check_confirm_checkbox()
                if not checked:
                    self._log("MH-FILL-ERR-CHECKBOX", "Confirmation checkbox is still unchecked after click")
                    self._save_debug_artifacts("checkbox_not_checked")
                    return False

            self.sb.sleep(1)
            submit_states = self._get_submit_candidate_states()
            if submit_states and all(state.get("disabled") for state in submit_states):
                self._log(
                    "MH-FILL-SUBMIT-LOCKED",
                    f"Submit still disabled after textarea+checkbox validation: {submit_states}",
                )
                attendance_retry = self._ensure_attendance_hadir()
                checkbox_retry = self._try_check_confirm_checkbox()
                self._log(
                    "MH-FILL-SUBMIT-RECOVER",
                    f"Recovery attempt for locked submit: attendance_ok={attendance_retry}, checkbox_ok={checkbox_retry}",
                )
                self.sb.sleep(1)
                submit_states = self._get_submit_candidate_states()
                if submit_states:
                    self._log("MH-FILL-SUBMIT-STATE", f"Submit state after recovery: {submit_states}")

            self._log("MH-FILL-OK", "Form filled")
            return True
        except Exception as e:
            self._log("MH-FILL-ERR-EXCEPTION", f"Failed to fill form: {e}")
            self._log("MH-FILL-TRACE", traceback.format_exc())
            self._save_debug_artifacts("fill_exception")
            return False

    def _submit(self) -> bool:
        try:
            self._log("MH-SUBMIT-START", "Submitting report")
            checkbox_state = self._get_confirm_checkbox_state()
            if checkbox_state.get("found") and not checkbox_state.get("checked"):
                self._log("MH-SUBMIT-ERR-CHECKBOX", "Submit blocked because confirmation checkbox is unchecked")
                self._save_debug_artifacts("submit_checkbox_unchecked")
                return False

            submit_button = self._find_enabled_submit_button(attempts=10, sleep_seconds=1, log_wait=True)
            if submit_button is None:
                self._log("MH-SUBMIT-RECOVER", "Submit locked. Retrying attendance + checkbox validation before failing.")
                attendance_retry = self._ensure_attendance_hadir()
                checkbox_retry = self._try_check_confirm_checkbox()
                self._log(
                    "MH-SUBMIT-RECOVER-STATE",
                    f"Recovery results: attendance_ok={attendance_retry}, checkbox_ok={checkbox_retry}",
                )
                submit_button = self._find_enabled_submit_button(attempts=5, sleep_seconds=1, log_wait=False)
            if submit_button is None:
                feedback = self._get_submit_feedback()
                self._log("MH-SUBMIT-LOCKED-DETAIL", f"Submit remained disabled; feedback={feedback}")
                self._log("MH-SUBMIT-ERR-BUTTON", "Submit button candidate not found in enabled state")
                self._save_debug_artifacts("submit_button_not_found")
                return False

            for click_attempt in range(2):
                try:
                    submit_button.click()
                except Exception:
                    self.sb.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", submit_button
                    )
                    self.sb.driver.execute_script("arguments[0].click();", submit_button)
                self._log("MH-SUBMIT-CLICK", f"Submit button clicked (attempt={click_attempt + 1})")

                # Validation: report dialog should close.
                for wait_idx in range(20):
                    dialog_state = self._get_report_dialog_state()
                    if not dialog_state.get("open"):
                        self._log("MH-SUBMIT-OK", "Report submitted successfully")
                        return True

                    if wait_idx in {4, 9, 14, 19}:
                        feedback = self._get_submit_feedback()
                        self._log(
                            "MH-SUBMIT-PENDING",
                            f"Dialog still open after {wait_idx + 1}s; feedback={feedback}",
                        )
                    self.sb.sleep(1)

                if click_attempt == 0:
                    feedback = self._get_submit_feedback()
                    can_retry_click = any(not btn.get("disabled") for btn in feedback.get("submitButtons", []))
                    if can_retry_click:
                        self._log("MH-SUBMIT-RETRY", "Retrying submit click because dialog remains open but button is enabled")
                        submit_button = self._find_enabled_submit_button(attempts=3, sleep_seconds=1, log_wait=False)
                        if submit_button is not None:
                            continue
                break

            final_feedback = self._get_submit_feedback()
            self._log("MH-SUBMIT-ERR-DETAIL", f"Dialog remained open after submit attempts; feedback={final_feedback}")
            self._log("MH-SUBMIT-ERR-DIALOG", "Dialog still visible after submit")
            self._save_debug_artifacts("submit_not_closed")
            return False
        except Exception as e:
            self._log("MH-SUBMIT-ERR-EXCEPTION", f"Failed to submit: {e}")
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
