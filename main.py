import logging
import traceback
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from app.config import config
from app.handlers import start, profile, menu, chat, history, profile_edit
from app.database import Base, engine
from app.scheduler import start_scheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Error Handler =====
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="⚠️ خطا:", exc_info=context.error)
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass

# ===== ساخت اپلیکیشن =====
app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ===== ثبت هندلرها =====
app.add_handler(CommandHandler("start", start.start))

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(profile.start_profile, pattern="start_profile")],
    states={
        profile.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_name)],
        profile.GENDER: [CallbackQueryHandler(profile.get_gender)],
        profile.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_age)],
        profile.STYLE: [CallbackQueryHandler(profile.get_style)]
    },
    fallbacks=[CommandHandler("start", start.start)],
    per_message=False
)
app.add_handler(conv_handler)

app.add_handler(CommandHandler("menu", menu.main_menu))
app.add_handler(CallbackQueryHandler(menu.main_menu, pattern="main_menu"))
app.add_handler(CallbackQueryHandler(menu.chat_menu, pattern="chat_menu"))
app.add_handler(CallbackQueryHandler(menu.history_menu, pattern="history_menu"))
app.add_handler(CallbackQueryHandler(menu.profile_menu, pattern="profile_menu"))

app.add_handler(CallbackQueryHandler(profile_edit.edit_name, pattern="edit_name"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_gender, pattern="edit_gender"))
app.add_handler(CallbackQueryHandler(profile_edit.set_gender, pattern="set_gender_"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_age, pattern="edit_age"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_style, pattern="edit_style"))
app.add_handler(CallbackQueryHandler(profile_edit.set_style, pattern="set_style_"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_notifications, pattern="edit_notifications"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_edit.handle_edit_input))
app.add_handler(CommandHandler("profile", profile_edit.show_profile))

app.add_handler(CallbackQueryHandler(history.record_mood, pattern="mood_"))
app.add_handler(CallbackQueryHandler(history.full_history, pattern="full_history"))
app.add_handler(CommandHandler("history", history.show_history))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

app.add_error_handler(error_handler)

# ===== راه‌اندازی Scheduler =====
start_scheduler()

# ===== اجرا با Webhook =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 ربات با Webhook روی پورت {port} راه‌اندازی شد!")
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=config.BOT_TOKEN,
        webhook_url=f"https://life-assistant-bot-24ef7.onrender.com/{config.BOT_TOKEN}"
    )
