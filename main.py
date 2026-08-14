import logging
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
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ایجاد جداول دیتابیس
Base.metadata.create_all(engine)

# ساخت اپلیکیشن
app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ===== ثبت هندلرها =====

# استارت
app.add_handler(CommandHandler("start", start.start))
app.add_handler(CallbackQueryHandler(start.start, pattern="main_menu"))

# پروفایل
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(profile.start_profile, pattern="start_profile")],
    states={
        profile.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_name)],
        profile.GENDER: [CallbackQueryHandler(profile.get_gender)],
        profile.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_age)],
        profile.STYLE: [CallbackQueryHandler(profile.get_style)]
    },
    fallbacks=[]
)
app.add_handler(conv_handler)
app.add_handler(CommandHandler("profile", profile.show_profile))

# چت با هوش مصنوعی
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

# یادآوری
app.add_handler(CommandHandler("remind", reminders.set_reminder))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'\d{4}-\d{2}-\d{2}'), reminders.process_reminder))
app.add_handler(CommandHandler("listreminders", reminders.list_reminders))

# بازی
app.add_handler(CommandHandler("game", game.start_game))
app.add_handler(CallbackQueryHandler(game.game_guess_letter, pattern="guess_letter"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, game.process_guess))
app.add_handler(CallbackQueryHandler(game.game_hint, pattern="game_hint"))
app.add_handler(CallbackQueryHandler(game.game_exit, pattern="game_exit"))

# تاریخچه احساسات
app.add_handler(CommandHandler("mood", history.record_mood))
app.add_handler(CommandHandler("history", history.show_history))
app.add_handler(CallbackQueryHandler(history.full_history, pattern="full_history"))

# مدیریت مالی
app.add_handler(CommandHandler("add", finance.add_transaction))
app.add_handler(CommandHandler("finance", finance.show_finance_report))
app.add_handler(CallbackQueryHandler(finance.buy_premium, pattern="buy_premium"))

# ===== زمان‌بندی پیام‌های خودکار =====
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tehran"))

async def send_morning_messages():
    # در نسخه کامل باید همه‌ی کاربران فعال رو از دیتابیس بخونی و بهشون پیام بدی
    pass

async def send_night_messages():
    # در نسخه کامل باید همه‌ی کاربران فعال رو از دیتابیس بخونی و بهشون پیام بدی
    pass

scheduler.add_job(send_morning_messages, 'cron', hour=7, minute=0)
scheduler.add_job(send_night_messages, 'cron', hour=23, minute=0)
scheduler.start()

# ===== اجرا =====
if __name__ == "__main__":
    print("🤖 ربات دستیار هوشمند راه‌اندازی شد!")
    app.run_polling()
