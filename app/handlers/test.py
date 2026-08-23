import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔥🔥🔥 test_handler اجرا شد! پیام: " + update.message.text)
    await update.message.reply_text("✅ پیام دریافت شد!")
