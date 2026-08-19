import logging
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
from app.handlers import (
    start, profile, menu, chat, history, profile_edit,
    predictor, past_self, therapist
)
from app.database import Base, engine
from app.scheduler import start_scheduler

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Error Handler =====
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="⚠️ خطا:", exc_info=context.error)
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass

# ===== ساخت اپلیکیشن =====
app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ============================================================
# 1. استارت
# ============================================================
app.add_handler(CommandHandler("start", start.start))

# ============================================================
# 2. ثبت‌نام
# ============================================================
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

# ============================================================
# 3. منو
# ============================================================
app.add_handler(CommandHandler("menu", menu.main_menu))
app.add_handler(CallbackQueryHandler(menu.main_menu, pattern="main_menu"))
app.add_handler(CallbackQueryHandler(menu.chat_menu, pattern="chat_menu"))
app.add_handler(CallbackQueryHandler(menu.predict_menu, pattern="predict_menu"))
app.add_handler(CallbackQueryHandler(menu.past_self_menu, pattern="past_self_menu"))
app.add_handler(CallbackQueryHandler(menu.therapy_menu, pattern="therapy_menu"))
app.add_handler(CallbackQueryHandler(menu.history_menu, pattern="history_menu"))
app.add_handler(CallbackQueryHandler(menu.profile_menu, pattern="profile_menu"))

# ============================================================
# 4. ویرایش پروفایل
# ============================================================
app.add_handler(CallbackQueryHandler(profile_edit.edit_name, pattern="edit_name"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_gender, pattern="edit_gender"))
app.add_handler(CallbackQueryHandler(profile_edit.set_gender, pattern="set_gender_"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_age, pattern="edit_age"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_style, pattern="edit_style"))
app.add_handler(CallbackQueryHandler(profile_edit.set_style, pattern="set_style_"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_notifications, pattern="edit_notifications"))
app.add_handler(CommandHandler("profile", profile_edit.show_profile))

# ============================================================
# 5. تاریخچه احساسات
# ============================================================
app.add_handler(CallbackQueryHandler(history.record_mood, pattern="mood_"))
app.add_handler(CallbackQueryHandler(history.full_history, pattern="full_history"))
app.add_handler(CommandHandler("history", history.show_history))

# ============================================================
# 6. پیش‌بینی
# ============================================================
app.add_handler(CallbackQueryHandler(predictor.predict_tomorrow, pattern="predict_tomorrow"))

# ============================================================
# 7. خود گذشته
# ============================================================
app.add_handler(CallbackQueryHandler(past_self.start_past_self, pattern="past_self_menu"))
app.add_handler(CallbackQueryHandler(past_self.show_answers, pattern="past_self_show_answers"))
app.add_handler(CallbackQueryHandler(past_self.delete_answers, pattern="past_self_delete_answers"))
app.add_handler(CallbackQueryHandler(past_self.new_interview, pattern="past_self_new_interview"))
app.add_handler(CallbackQueryHandler(past_self.end_interview_early, pattern="past_self_end_interview"))
app.add_handler(CallbackQueryHandler(past_self.free_chat, pattern="past_self_free_chat"))
app.add_handler(CallbackQueryHandler(past_self.end_free_chat, pattern="past_self_end_free_chat"))

# ============================================================
# 8. درمانگر
# ============================================================
app.add_handler(CallbackQueryHandler(therapist.end_therapy, pattern="end_therapy"))

# ============================================================
# 9. MessageHandlerهای تخصصی
# ============================================================
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, past_self.receive_answer))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, past_self.chat_with_past_self))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, therapist.chat_with_therapist))

# ============================================================
# 10. گفتگو با دستیار (آخرین اولویت)
# ============================================================
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

# ============================================================
# Error Handler
# ============================================================
app.add_error_handler(error_handler)

# ============================================================
# ایجاد جداول دیتابیس
# ============================================================
Base.metadata.create_all(engine)

# ============================================================
# Scheduler
# ============================================================
start_scheduler()

# ============================================================
# اجرا با Webhook
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/{config.BOT_TOKEN}"
    
    logger.info(f"🚀 ربات با Webhook روی پورت {port} راه‌اندازی شد!")
    logger.info(f"🔗 Webhook URL: {webhook_url}")
    
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=config.BOT_TOKEN,
        webhook_url=webhook_url
)
