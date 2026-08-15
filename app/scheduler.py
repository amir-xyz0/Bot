from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
from app.config import config
from app.database import SessionLocal
from app.models import User
import pytz
import asyncio

scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Tehran"))

async def send_morning_messages():
    bot = Bot(token=config.BOT_TOKEN)
    db = SessionLocal()
    users = db.query(User).filter_by(morning_msg_enabled=True).all()
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.user_id,
                text="🌅 صبح بخیر! روز خوبی را برای شما آرزو میکنم."
            )
        except:
            pass
    db.close()

async def send_night_messages():
    bot = Bot(token=config.BOT_TOKEN)
    db = SessionLocal()
    users = db.query(User).filter_by(night_msg_enabled=True).all()
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.user_id,
                text="🌙 شب بخیر! خواب آرامی داشته باشید."
            )
        except:
            pass
    db.close()

def morning_wrapper():
    asyncio.run(send_morning_messages())

def night_wrapper():
    asyncio.run(send_night_messages())

scheduler.add_job(morning_wrapper, 'cron', hour=7, minute=0)
scheduler.add_job(night_wrapper, 'cron', hour=23, minute=0)
