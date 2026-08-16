import logging
import traceback
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
from app.handlers import start, profile, menu, chat, history, profile_edit
from app.database import Base, engine
from app.scheduler import start_scheduler
from datetime import datetime
import pytz

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# Error Handler
# ============================================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت خطاهای ثبت‌نشده"""
    logger.error(msg="⚠️ خطا در به‌روزرسانی:", exc_info=context.error)
    
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    logger.error(f"📄 جزئیات کامل:\n{tb_string}")
    
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ خطایی رخ داد. تیم فنی در جریان قرار گرفت و به زودی رفع خواهد شد."
            )
        except:
            pass

# ============================================================
# ساخت اپلیکیشن
# ============================================================
app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ============================================================
# 1. استارت
# ============================================================
app.add_handler(CommandHandler("start", start.start))

# ============================================================
# 2. ثبت‌نام (پروفایل) - ConversationHandler
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
# 3. منوی اصلی
# ============================================================
app.add_handler(CommandHandler("menu", menu.main_menu))
app.add_handler(CallbackQueryHandler(menu.main_menu, pattern="main_menu"))
app.add_handler(CallbackQueryHandler(menu.chat_menu, pattern="chat_menu"))
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
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_edit.handle_edit_input))
app.add_handler(CommandHandler("profile", profile_edit.show_profile))

# ============================================================
# 5. تاریخچه احساسات
# ============================================================
app.add_handler(CallbackQueryHandler(history.record_mood, pattern="mood_"))
app.add_handler(CallbackQueryHandler(history.full_history, pattern="full_history"))
app.add_handler(CommandHandler("history", history.show_history))

# ============================================================
# 6. گفتگو با دستیار (MessageHandler عمومی - آخرین اولویت)
# ============================================================
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

# ============================================================
# ثبت Error Handler
# ============================================================
app.add_error_handler(error_handler)

# ============================================================
# وب سرور برای Render (جلوگیری از خوابیدن سرویس)
# ============================================================
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

# ============================================================
# راه‌اندازی Scheduler (ارسال پیام‌های خودکار)
# ============================================================
start_scheduler()

# ============================================================
# اجرای اصلی ربات
# ============================================================
if __name__ == "__main__":
    print("🚀 ربات دستیار هوشمند راه‌اندازی شد!")
    print(f"⏰ زمان سرور: {datetime.now(pytz.timezone('Asia/Tehran')).strftime('%Y-%m-%d %H:%M:%S')}")
    # poll_interval=2.0 برای کاهش ترافیک و timeout=10 برای پاسخ‌دهی سریع‌تر
    app.run_polling(poll_interval=2.0, timeout=10, allowed_updates=None)
