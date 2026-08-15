import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
from app.config import config
from app.handlers import start, profile, menu, chat, reminders, history, profile_edit
from app.database import Base, engine
from app.scheduler import start_scheduler

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ایجاد جداول دیتابیس
Base.metadata.create_all(engine)

# ساخت اپلیکیشن
app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ============================================================
# 1. استارت (صفحه خوش‌آمدگویی قبل از ثبت‌نام)
# ============================================================
app.add_handler(CommandHandler("start", start.start))

# ============================================================
# 2. ثبت‌نام (پروفایل) - با ConversationHandler
# ============================================================
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
    per_message=True
)
app.add_handler(conv_handler)

# ============================================================
# 3. منوی اصلی (دکمه‌های شیشه‌ای)
# ============================================================
app.add_handler(CommandHandler("menu", menu.main_menu))
app.add_handler(CallbackQueryHandler(menu.main_menu, pattern="main_menu"))
app.add_handler(CallbackQueryHandler(menu.chat_menu, pattern="chat_menu"))
app.add_handler(CallbackQueryHandler(menu.reminder_menu, pattern="reminder_menu"))
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
# 6. یادآوری‌ها (با ConversationHandler و دکمه‌های سریع)
# ============================================================
reminder_conv = ConversationHandler(
    entry_points=[CommandHandler("remind", reminders.set_reminder)],
    states={
        reminders.DATE: [
            CallbackQueryHandler(reminders.quick_date_selected, pattern="^quick_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, reminders.get_manual_date)
        ],
        reminders.TIME: [
            CallbackQueryHandler(reminders.quick_time_selected, pattern="^time_"),
            CallbackQueryHandler(reminders.back_to_date, pattern="^back_to_date$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, reminders.get_manual_time)
        ],
        reminders.TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminders.get_title)]
    },
    fallbacks=[
        CommandHandler("start", start.start),
        CommandHandler("cancel", start.start)
    ],
    per_message=True
)
app.add_handler(reminder_conv)
app.add_handler(CommandHandler("listreminders", reminders.list_reminders))
app.add_handler(CommandHandler("cancel_reminder", reminders.cancel_reminder))

# ============================================================
# 7. گفتگو با دستیار (فقط در بخش چت فعال است)
# ============================================================
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

# ============================================================
# 8. وب سرور ساده برای جلوگیری از خوابیدن Render
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
# 9. راه‌اندازی Scheduler (اعلان‌های صبح، شب و غیبت)
# ============================================================
start_scheduler()

# ============================================================
# 10. اجرای اصلی ربات با Polling
# ============================================================
if __name__ == "__main__":
    print("🚀 ربات دستیار هوشمند راه‌اندازی شد!")
    app.run_polling(poll_interval=3.0, timeout=20, allowed_updates=None)
