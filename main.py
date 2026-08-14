import logging
import os
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
from app.config import config
from app.handlers import start, profile, chat, reminders, game, history, finance
from app.database import Base, engine

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

Base.metadata.create_all(engine)

app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ===== ثبت هندلرها =====
app.add_handler(CommandHandler("start", start.start))
app.add_handler(CallbackQueryHandler(start.start, pattern="main_menu"))

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

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

app.add_handler(CommandHandler("remind", reminders.set_reminder))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'\d{4}-\d{2}-\d{2}'), reminders.process_reminder))
app.add_handler(CommandHandler("listreminders", reminders.list_reminders))
app.add_handler(CommandHandler("cancel_reminder", reminders.cancel_reminder))

app.add_handler(CommandHandler("game", game.start_game))
app.add_handler(CallbackQueryHandler(game.game_guess_letter, pattern="guess_letter"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, game.process_guess))
app.add_handler(CallbackQueryHandler(game.game_hint, pattern="game_hint"))
app.add_handler(CallbackQueryHandler(game.game_exit, pattern="game_exit"))

app.add_handler(CommandHandler("mood", history.record_mood))
app.add_handler(CommandHandler("history", history.show_history))
app.add_handler(CallbackQueryHandler(history.full_history, pattern="full_history"))

app.add_handler(CommandHandler("add", finance.add_transaction))
app.add_handler(CommandHandler("finance", finance.show_finance_report))
app.add_handler(CallbackQueryHandler(finance.buy_premium, pattern="buy_premium"))

# ===== اجرا با Webhook =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🤖 ربات روی پورت {port} راه‌اندازی شد!")
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=config.BOT_TOKEN,
        webhook_url=f"https://life-assistant-bot.onrender.com/{config.BOT_TOKEN}"
    )
