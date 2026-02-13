import os
import sys
from dotenv import load_dotenv

# Add project root to path to ensure imports work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.infrastructure.ai.openrouter_ai import OpenRouterAI
from src.infrastructure.automation.seleniumbase_driver import SeleniumBaseDriver
from src.services.report_service import ReportService

from src.config import config

def main():
    if not config:
        return

    # User Input
    print(f"📝 Apa aktivitasmu hari ini? (Context: {config.aktivitas_konteks})")
    activity = input("> ").strip()
    if not activity:
        print("❌ Activity cannot be empty.")
        return

    # Dependency Injection
    # We inject the concrete implementations here (Composition Root)
    ai_provider = OpenRouterAI(
        api_key=config.openrouter_api_key,
        model=config.ai_model,
    )
    
    # Logic inversion: Show Browser = True -> Headless = False
    is_headless = not config.show_browser
    
    automation_driver = SeleniumBaseDriver(headless=is_headless)
    
    service = ReportService(ai_provider, automation_driver)
    
    # Execute
    service.process_daily_report(config.aktivitas_konteks, activity, config.maganghub_email, config.maganghub_password)

if __name__ == "__main__":
    main()
