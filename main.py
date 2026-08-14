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
from app.handlers import start, profile, chat, reminders, game, history
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

# ثبت هندلرها
app.add_handler(CommandHandler("start", start.start))
app.add_handler(CallbackQueryHandler(start.start, pattern="main_menu"))

# ثبت ConversationHandler برای پروفایل
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

# چت با هوش مصنوعی
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.chat_with_ai))

# یادآوری
app.add_handler(CommandHandler("remind", reminders.set_reminder))

# بازی
app.add_handler(CommandHandler("game", game.start_game))

# تاریخچه
app.add_handler(CommandHandler("history", history.show_history))

# زمان‌بندی پیام‌های خودکار
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tehran"))

async def morning_message(context):
    # منطق ارسال پیام صبح
    pass

async def night_message(context):
    # منطق ارسال پیام شب
    pass

scheduler.add_job(morning_message, 'cron', hour=7, minute=0)
scheduler.add_job(night_message, 'cron', hour=23, minute=0)
scheduler.start()

if __name__ == "__main__":
    app.run_polling()
