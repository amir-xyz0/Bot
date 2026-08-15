import logging
import os
import threading
import time
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
from app.handlers import start, profile, chat, reminders, game, history, finance, menu
from app.database import Base, engine

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

Base.metadata.create_all(engine)

app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ===== هندلرهای منو =====
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

# ===== چت =====
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

# ===== یادآوری =====
app.add_handler(CommandHandler("remind", reminders.set_reminder))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'\d{4}-\d{2}-\d{2}'), reminders.process_reminder))
app.add_handler(CommandHandler("listreminders", reminders.list_reminders))
app.add_handler(CommandHandler("cancel_reminder", reminders.cancel_reminder))

# ===== بازی =====
app.add_handler(CommandHandler("game", game.start_game))
app.add_handler(CallbackQueryHandler(game.game_guess_letter, pattern="guess_letter"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, game.process_guess))
app.add_handler(CallbackQueryHandler(game.game_hint, pattern="game_hint"))
app.add_handler(CallbackQueryHandler(game.game_exit, pattern="game_exit"))

# ===== تاریخچه =====
app.add_handler(CommandHandler("mood", history.record_mood))
app.add_handler(CommandHandler("history", history.show_history))
app.add_handler(CallbackQueryHandler(history.full_history, pattern="full_history"))

# ===== مالی =====
app.add_handler(CommandHandler("add", finance.add_transaction))
app.add_handler(CommandHandler("finance", finance.show_finance_report))
app.add_handler(CallbackQueryHandler(finance.buy_premium, pattern="buy_premium"))

# ===== وب سرور برای رندر =====
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

thread = threading.Thread(target=run_http_server, daemon=True)
thread.start()

# ===== اجرا =====
if __name__ == "__main__":
    print("🤖 ربات با Polling راه‌اندازی شد!")
    app.run_polling()
