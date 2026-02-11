import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from src.core.interfaces import IInteractionHandler, IContentGenerator, IAutomationDriver
from src.services.report_service import ReportService
from src.config import config

# Setup logging
logger = logging.getLogger(__name__)

class TelegramBotHandler(IInteractionHandler):
    """
    Handles Telegram interactions.
    Requires TELEGRAM_BOT_TOKEN in .env
    """
    def __init__(self, token: str, report_service: ReportService):
        self.token = token
        self.service = report_service
        self.app = ApplicationBuilder().token(token).build()
        
        # Register handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 AutoAbsen Bot Ready!\n\n"
            "Just send me your daily activity, and I will:\n" 
            "1. Generate a full report using AI\n"
            "2. Submit it to MagangHub automatically.\n\n"
            "Try sending: 'Fixing login bug and learning Docker'"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Commands:\n"
            "/start - Start the bot\n"
            "Just type your activity to submit a report."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_text = update.message.text
        user_id = update.effective_user.id
        
        # Security: Only allow specific users if needed (optional)
        # if str(user_id) != config.allowed_telegram_id: return

        await update.message.reply_text("⏳ Processing your report... (This simulates browsing, might take 1-2 mins)")
        
        # Run synchronous service logic in a separate thread to not block the bot
        # automation is blocking, so we need run_in_executor
        loop = asyncio.get_running_loop()
        
        try:
            # We need to pass the context explicitly or rely on global config
            # Here we assume single-user config for now (SOLID: we should probably pass user credentials here)
            success = await loop.run_in_executor(
                None, 
                self.service.process_daily_report,
                config.aktivitas_konteks,
                user_text, 
                config.maganghub_email, 
                config.maganghub_password
            )
            
            if success:
                await update.message.reply_text("✅ Report Submitted Successfully! 🎉")
            else:
                await update.message.reply_text("❌ Report Submission Failed. Check logs.")
                
        except Exception as e:
            logger.error(f"Bot Error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    def start(self):
        """Run the bot (blocking)"""
        print("🤖 Telegram Bot Started...")
        self.app.run_polling()

    def stop(self):
        pass
