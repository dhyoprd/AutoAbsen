import os
import sys
import logging
import asyncio
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.ai.openrouter_ai import OpenRouterAI
from src.infrastructure.automation.seleniumbase_driver import SeleniumBaseDriver
from src.services.report_service import ReportService
from src.config import config
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)

class WorkflowBot:
    """
    Short-lived bot for workflow interactions.
    It will run for a max duration (e.g. 15 mins) and exit.
    """
    def __init__(self):
        self.app = ApplicationBuilder().token(config.telegram_bot_token).build()
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message))
        self.interaction_complete = False
        self.start_time = time.time()
        self.MAX_DURATION = 900  # 15 minutes timeout
        
        # Dependency Injection
        self.ai = OpenRouterAI(
            api_key=config.openrouter_api_key,
            model=config.ai_model,
        )
        self.service = None 
        # Delayed init for driver to save resources if no input
        
        # State
        self.state = "WAITING_FOR_INPUT" # -> WAITING_CONFIRM -> DONE
        self.draft_report = None
        self.draft_context = None

    async def notify_user(self):
        """Send initial ping"""
        try:
            msg = await self.app.bot.send_message(
                chat_id=config.allowed_telegram_id,
                text="🔔 **AutoAbsen Reminder**\n\n"
                     "It's 4 PM! What did you do today?\n"
                     "Reply to this message within 15 minutes to generate your report."
            )
            logger.info(f"Notification sent to {config.allowed_telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            self.interaction_complete = True # Exit if we can't notify

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if user_id != config.allowed_telegram_id:
            await update.message.reply_text("⛔ Unauthorized.")
            return

        text = update.message.text
        
        if self.state == "WAITING_FOR_INPUT":
            await update.message.reply_text("⏳ Generating draft report... please wait.")
            
            # Generate Report
            try:
                # We reuse the AI logic directly here to just get the object first
                # Or use service but we need to split generation and submission.
                # Let's use AI directly for "Draft" step.
                report = self.ai.generate_content(config.aktivitas_konteks, text)
                
                if not report.validate():
                    await update.message.reply_text("❌ Generated report was too short. Please try again with more details.")
                    return

                self.draft_report = report
                self.draft_context = text
                self.state = "WAITING_CONFIRM"
                
                # Send back for double check
                response_text = (
                    "**✅ Draft Report Generated**\n\n"
                    f"**Activity:**\n{report.activity}\n\n"
                    f"**Learning:**\n{report.learning}\n\n"
                    f"**Obstacles:**\n{report.obstacles}\n\n"
                    "-----------------------------\n"
                    "Reply **'YES'** to submit this report.\n"
                    "Reply **'CANCEL'** to stop.\n"
                    "Reply anything else to regenerate."
                )
                await update.message.reply_text(response_text, parse_mode="Markdown")
                
            except Exception as e:
                logger.error(f"Generation error: {e}")
                await update.message.reply_text("❌ Error generating report. Try again.")

        elif self.state == "WAITING_CONFIRM":
            if text.upper().strip() == "YES":
                await update.message.reply_text("🚀 Submitting report... (Selenium launching)")
                
                # Launch Selenium (Only now to save memory/time)
                try:
                    is_headless = True # Always headless in CI
                    driver = SeleniumBaseDriver(headless=is_headless)
                    service = ReportService(self.ai, driver)
                    
                    # Run logic (blocking call needs executor)
                    loop = asyncio.get_running_loop()
                    success = await loop.run_in_executor(
                        None,
                        self.service_submit_wrapper,
                        service,
                        self.draft_report
                    )
                    
                    if success:
                        await update.message.reply_text("🎉 Report Submitted Successfully!")
                    else:
                        await update.message.reply_text("❌ Submission Failed. Check GitHub Actions logs.")
                        
                except Exception as e:
                    await update.message.reply_text(f"❌ Automation Error: {e}")
                
                self.interaction_complete = True
                
            elif text.upper().strip() == "CANCEL":
                await update.message.reply_text("🚫 Operation cancelled.")
                self.interaction_complete = True
            else:
                # Treat as new input -> Regenerate
                self.state = "WAITING_FOR_INPUT"
                await self.handle_message(update, context)

    def service_submit_wrapper(self, service, report):
        """Helper to call service submit directly since we already have the report object"""
        # We only need submit here because draft is already generated.
        return service.driver.execute_full_flow(
            config.maganghub_email,
            config.maganghub_password,
            report
        )

    async def run(self):
        """Main loop with timeout"""
        await self.app.initialize()
        await self.app.start()
        await self.notify_user()
        await self.app.updater.start_polling()
        
        while not self.interaction_complete:
            if time.time() - self.start_time > self.MAX_DURATION:
                logger.warning("Timeout reached. Exiting.")
                try:
                    await self.app.bot.send_message(
                        chat_id=config.allowed_telegram_id,
                        text="⏳ **Timeout**: You didn't reply in time. Workflow exiting."
                    )
                except:
                    pass
                break
            await asyncio.sleep(1)
            
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()

async def main_async():
    setup_logger()
    if not config.telegram_bot_token or not config.allowed_telegram_id:
        logger.error("Missing Telegram Config")
        return
        
    bot = WorkflowBot()
    await bot.run()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
