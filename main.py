import logging
import os
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
from app.handlers import start, profile, chat, menu
from app.database import Base, engine
from app.scheduler import scheduler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
Base.metadata.create_all(engine)

app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ===== منو =====
app.add_handler(CommandHandler("menu", menu.main_menu))
app.add_handler(CallbackQueryHandler(menu.main_menu, pattern="main_menu"))
app.add_handler(CallbackQueryHandler(menu.chat_menu, pattern="chat_menu"))
app.add_handler(CallbackQueryHandler(menu.reminder_menu, pattern="reminder_menu"))
app.add_handler(CallbackQueryHandler(menu.history_menu, pattern="history_menu"))
app.add_handler(CallbackQueryHandler(menu.profile_menu, pattern="profile_menu"))

# ===== استارت =====
app.add_handler(CommandHandler("start", start.start))

# ===== پروفایل =====
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(profile.start_profile, pattern="start_profile")],
    states={
        profile.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_name)],
        profile.GENDER: [CallbackQueryHandler(profile.get_gender)],
        profile.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_age)],
        profile.STYLE: [CallbackQueryHandler(profile.get_style)]
    },
    fallbacks=[],
    per_message=True
)
app.add_handler(conv_handler)
app.add_handler(CommandHandler("profile", profile.show_profile))

# ===== چت (فقط در بخش چت) =====
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

# ===== وب سرور برای رندر =====
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()

# ===== استارت Scheduler =====
scheduler.start()

# ===== اجرا با تنظیمات دقیق Polling =====
if __name__ == "__main__":
    print("ربات راه‌اندازی شد!")
    app.run_polling(poll_interval=5.0, timeout=30, allowed_updates=None)
