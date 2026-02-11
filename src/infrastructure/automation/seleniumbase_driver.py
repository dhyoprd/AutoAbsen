import time
from typing import Optional
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
        self.sb_context = None
        self.driver = None

    def run_with_sb(self, action_callback):
        """Helper to run code within SB context if not already running."""
        # Note: SeleniumBase usually runs as a context manager.
        # For this design pattern where we need persistent state across methods,
        # we might need to structure it differently or re-initialize.
        # However, for simplicity in this refactor, we'll use a single session method 
        # that orchestrates the flow, OR we adapted the interface to be a context manager itself.
        # To strictly follow the Interface which has separate methods, we'll need to instantiate SB 
        # and keep the driver alive. SB's `Driver()` class is useful here.
        pass

    def execute_full_flow(self, email: str, password: str, report: Report):
        """
        Executes the full automation flow in a single SB context to ensure stability.
        This is a deviation from strict granular interface methods for the sake of 
        SeleniumBase's 'with SB()' pattern which is robust.
        """
        with SB(uc=True, headless=self.headless, test=True) as sb:
            self.sb = sb  # Assign to self for helper methods to use
            
            # 1. Login
            if not self._login(email, password):
                return False
                
            # 2. Navigate to Form
            if not self._navigate_to_today():
                return False
                
            # 3. Fill Report
            if not self._fill_form(report):
                return False
                
            # 4. Submit
            if not self._submit():
                return False
                
            return True

    def _login(self, email: str, password: str) -> bool:
        try:
            print("→ Opening Login Page...")
            self.sb.open(Sel.LOGIN_URL)
            self.sb.type(Sel.USERNAME_INPUT, email)
            self.sb.type(Sel.PASSWORD_INPUT, password)
            self.sb.click(Sel.LOGIN_BUTTON)
            
            # Wait for dashboard
            self.sb.wait_for_element_visible("nav, .dashboard, .v-main", timeout=15)
            if "dashboard" in self.sb.get_current_url() or "monev" in self.sb.get_current_url():
                print("✓ Login successful")
                return True
            return False
        except Exception as e:
            print(f"✗ Login failed: {e}")
            return False

    def _navigate_to_today(self) -> bool:
        try:
            print("→ Navigating to Today's Report...")
            # Assuming we are on dashboard with calendar
            self.sb.wait_for_element_clickable(Sel.CALENDAR_TODAY_CELL, timeout=10)
            self.sb.click(Sel.CALENDAR_TODAY_CELL)
            
            # Wait for dialog
            self.sb.wait_for_element_visible(Sel.DIALOG_CONTAINER, timeout=5)
            print("✓ Report dialog opened")
            return True
        except Exception as e:
            print(f"✗ Failed to open report dialog: {e}")
            return False

    def _fill_form(self, report: Report) -> bool:
        try:
            print("→ Filling Report Form...")
            # Fill textareas
            textareas = self.sb.find_elements(Sel.TEXTAREA)
            if len(textareas) >= 3:
                textareas[0].send_keys(report.activity)
                textareas[1].send_keys(report.learning)
                textareas[2].send_keys(report.obstacles)
            else:
                print("⚠ Not enough textareas found!")
                return False
            
            # Checkbox
            # SB's click is robust, tries to scroll into view
            self.sb.click(Sel.CHECKBOX)
            
            print("✓ Form filled")
            return True
        except Exception as e:
            print(f"✗ Failed to fill form: {e}")
            return False

    def _submit(self) -> bool:
        try:
            print("→ Submitting Report...")
            self.sb.click(Sel.SUBMIT_BUTTON)
            self.sb.sleep(3) # Wait for network
            
            # Validation: check if dialog closed
            if self.sb.is_element_not_visible(Sel.DIALOG_CONTAINER):
                print("✓ Report submitted successfully")
                return True
            else:
                print("⚠ Dialog still visible, submit might have failed")
                return False
        except Exception as e:
            print(f"✗ Failed to submit: {e}")
            return False

    # Interface methods (Adapter pattern to fit the monolithic execution if needed)
    # For now, we mainly expose `execute_full_flow` which is more pythonic for SeleniumBase
    def login(self, email, password): pass 
    def navigate_to_report_page(self): pass
    def fill_report(self, report): pass
    def submit_report(self): pass
    def close(self): pass
