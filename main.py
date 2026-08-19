import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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
from datetime import datetime
import pytz
import requests

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="⚠️ خطا:", exc_info=context.error)
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass

# ===== ساخت اپلیکیشن =====
app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ===== 1. استارت =====
app.add_handler(CommandHandler("start", start.start))

# ===== 2. ثبت‌نام =====
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(profile.start_profile, pattern="start_profile")],
    states={
        profile.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_name)],
        profile.GENDER: [CallbackQueryHandler(profile.get_gender)],
        profile.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_age)],
        profile.STYLE: [CallbackQueryHandler(profile.get_style)]
    },
    fallbacks=[
        CommandHandler("start", start.start),
        CommandHandler("cancel", start.start)
    ],
    per_message=False
)
app.add_handler(conv_handler)

# ===== 3. منوی اصلی =====
app.add_handler(CommandHandler("menu", menu.main_menu))
app.add_handler(CallbackQueryHandler(menu.main_menu, pattern="main_menu"))
app.add_handler(CallbackQueryHandler(menu.chat_menu, pattern="chat_menu"))
app.add_handler(CallbackQueryHandler(menu.predict_menu, pattern="predict_menu"))
app.add_handler(CallbackQueryHandler(menu.past_self_menu, pattern="past_self_menu"))
app.add_handler(CallbackQueryHandler(menu.therapy_menu, pattern="therapy_menu"))
app.add_handler(CallbackQueryHandler(menu.history_menu, pattern="history_menu"))
app.add_handler(CallbackQueryHandler(menu.profile_menu, pattern="profile_menu"))

# ===== 4. ویرایش پروفایل =====
app.add_handler(CallbackQueryHandler(profile_edit.edit_name, pattern="edit_name"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_gender, pattern="edit_gender"))
app.add_handler(CallbackQueryHandler(profile_edit.set_gender, pattern="set_gender_"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_age, pattern="edit_age"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_style, pattern="edit_style"))
app.add_handler(CallbackQueryHandler(profile_edit.set_style, pattern="set_style_"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_notifications, pattern="edit_notifications"))
app.add_handler(CommandHandler("profile", profile_edit.show_profile))

# ===== 5. تاریخچه احساسات =====
app.add_handler(CallbackQueryHandler(history.record_mood, pattern="mood_"))
app.add_handler(CallbackQueryHandler(history.full_history, pattern="full_history"))
app.add_handler(CommandHandler("history", history.show_history))

# ===== 6. پیش‌بینی روز =====
app.add_handler(CallbackQueryHandler(predictor.predict_tomorrow, pattern="predict_tomorrow"))

# ===== 7. خود گذشته =====
app.add_handler(CallbackQueryHandler(past_self.start_past_self, pattern="past_self_menu"))
app.add_handler(CallbackQueryHandler(past_self.show_answers, pattern="past_self_show_answers"))
app.add_handler(CallbackQueryHandler(past_self.delete_answers, pattern="past_self_delete_answers"))
app.add_handler(CallbackQueryHandler(past_self.new_interview, pattern="past_self_new_interview"))
app.add_handler(CallbackQueryHandler(past_self.end_interview_early, pattern="past_self_end_interview"))
app.add_handler(CallbackQueryHandler(past_self.free_chat, pattern="past_self_free_chat"))
app.add_handler(CallbackQueryHandler(past_self.end_free_chat, pattern="past_self_end_free_chat"))

# ===== 8. درمانگر شناختی =====
app.add_handler(CallbackQueryHandler(therapist.end_therapy, pattern="end_therapy"))

# ===== 9. MessageHandlerهای تخصصی (با شرط داخلی) =====
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, past_self.receive_answer))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, past_self.chat_with_past_self))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, therapist.chat_with_therapist))

# ===== 10. گفتگو با دستیار (آخرین اولویت) =====
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

# ===== Error Handler =====
app.add_error_handler(error_handler)

# ===== وب سرور =====
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

# ===== Scheduler =====
start_scheduler()

# ===== اجرا =====
if __name__ == "__main__":
    # حذف Webhook برای جلوگیری از Conflict
    try:
        requests.get(f"https://api.telegram.org/bot{config.BOT_TOKEN}/deleteWebhook")
        logger.info("✅ Webhook deleted")
    except Exception as e:
        logger.warning(f"⚠️ خطا در حذف Webhook: {e}")
    
    Base.metadata.create_all(engine)
    print("🚀 ربات دستیار هوشمند راه‌اندازی شد!")
    print(f"⏰ زمان سرور: {datetime.now(pytz.timezone('Asia/Tehran')).strftime('%Y-%m-%d %H:%M:%S')}")
    app.run_polling(poll_interval=2.0, timeout=10, allowed_updates=None)
