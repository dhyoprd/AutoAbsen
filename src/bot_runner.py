import os
import sys
import logging

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.ai.openrouter_ai import OpenRouterAI
from src.infrastructure.automation.seleniumbase_driver import SeleniumBaseDriver
from src.infrastructure.telegram.bot import TelegramBotHandler
from src.services.report_service import ReportService
from src.config import config
from src.utils.logger import setup_logger

def main():
    setup_logger()
    logger = logging.getLogger(__name__)

    if not config.telegram_bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN is missing in .env")
        print("Please add TELEGRAM_BOT_TOKEN=your_token to .env")
        return

    logger.info("🤖 Starting AutoAbsen Telegram Bot...")

    # Dependency Injection
    ai_provider = OpenRouterAI(api_key=config.openrouter_api_key)
    # For bot, we usually want headless=True
    is_headless = not config.show_browser
    automation_driver = SeleniumBaseDriver(headless=is_headless)
    
    service = ReportService(ai_provider, automation_driver)
    
    # Init Bot
    try:
        # Create bot handler
        # Note: ReportService is passed inside cause we want single instance
        bot = TelegramBotHandler(config.telegram_bot_token, service)
        bot.start()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
