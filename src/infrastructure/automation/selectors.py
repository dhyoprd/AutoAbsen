class MagangHubSelectors:
    """
    Centralized configuration for MagangHub selectors.
    Follows OCP: If page structure changes, only this file needs updates.
    """
    BASE_URL = "https://monev.maganghub.kemnaker.go.id"
    LOGIN_URL = f"{BASE_URL}/login"
    DASHBOARD_URL = f"{BASE_URL}/dashboard"
    
    # Login Page
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    LOGIN_BUTTON = "button[type='submit']"
    
    # Dashboard / Calendar
    # Combining multiple potential selectors for robustness
    CALENDAR_TODAY_CELL = "td.clickable-day.today-highlight, td.today-highlight, .v-date-picker-month__day--selected"
    
    # Report Form
    DIALOG_CONTAINER = ".v-dialog, .v-overlay-container"
    KEHADIRAN_DROPDOWN = ".v-select, [role='combobox']"
    HADIR_OPTION = "//div[contains(@class, 'v-list-item') and contains(text(), 'Hadir')] | //option[contains(text(), 'Hadir')]"
    
    TEXTAREA = "textarea"
    CHECKBOX = "input[type='checkbox']"
    
    SUBMIT_BUTTON = "//button[contains(text(), 'Simpan')] | //button[contains(text(), 'Kirim')] | //button[@type='submit']"
