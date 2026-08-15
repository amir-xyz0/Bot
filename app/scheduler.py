from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from app.config import config
from app.database import SessionLocal
from app.models import User, Reminder
from app.messages import get_morning_message, get_night_message, get_absent_message
import pytz
import asyncio
from datetime import datetime, timedelta

scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Tehran"))

async def send_morning_messages():
    """ارسال پیام صبح بخیر + انگیزشی"""
    bot = Bot(token=config.BOT_TOKEN)
    db = SessionLocal()
    users = db.query(User).filter_by(morning_msg_enabled=True, is_active=True).all()
    
    for user in users:
        try:
            text = (
                f"🌅 **صبح بخیر {user.preferred_name}!**\n\n"
                f"{get_morning_message(user.gender)}\n\n"
                f"امیدوارم امروز روز خوبی داشته باشی. 🌟"
            )
            await bot.send_message(chat_id=user.user_id, text=text)
        except Exception as e:
            print(f"Error sending morning to {user.user_id}: {e}")
    db.close()

async def send_night_messages():
    """ارسال پیام شب بخیر + پرسش از احساسات"""
    bot = Bot(token=config.BOT_TOKEN)
    db = SessionLocal()
    users = db.query(User).filter_by(night_msg_enabled=True, is_active=True).all()
    
    for user in users:
        try:
            keyboard = [
                [
                    InlineKeyboardButton("😊 خوب", callback_data="mood_good"),
                    InlineKeyboardButton("😐 معمولی", callback_data="mood_normal"),
                    InlineKeyboardButton("😔 بد", callback_data="mood_bad")
                ]
            ]
            text = (
                f"🌙 **شب بخیر {user.preferred_name}!**\n\n"
                f"{get_night_message()}\n\n"
                f"روزت چطور بود؟"
            )
            await bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            print(f"Error sending night to {user.user_id}: {e}")
    db.close()

async def check_absent_users():
    """بررسی کاربرانی که ۳ روز سر نزده‌اند"""
    bot = Bot(token=config.BOT_TOKEN)
    db = SessionLocal()
    three_days_ago = datetime.now(pytz.timezone("Asia/Tehran")) - timedelta(days=3)
    users = db.query(User).filter(
        User.is_active == True,
        User.last_activity < three_days_ago
    ).all()
    
    for user in users:
        try:
            text = (
                f"👋 **سلام {user.preferred_name}!**\n\n"
                f"{get_absent_message()}\n\n"
                f"هر وقت خواستی، برگرد که دلم برات تنگ شده. 💙"
            )
            await bot.send_message(chat_id=user.user_id, text=text)
            # به‌روزرسانی last_activity برای جلوگیری از ارسال مجدد
            user.last_activity = datetime.now(pytz.timezone("Asia/Tehran"))
            db.commit()
        except Exception as e:
            print(f"Error sending absent to {user.user_id}: {e}")
    db.close()

async def send_reminder(user_id: int, title: str, reminder_id: int, bot_token: str):
    """ارسال پیام یادآوری"""
    bot = Bot(token=bot_token)
    try:
        text = (
            f"⏰ **یادآوری!**\n\n"
            f"{title}\n\n"
            f"زمانش رسیده است. 🕐"
        )
        await bot.send_message(chat_id=user_id, text=text)
        
        # غیرفعال کردن یادآوری
        db = SessionLocal()
        reminder = db.query(Reminder).filter_by(id=reminder_id).first()
        if reminder:
            reminder.is_active = False
            db.commit()
        db.close()
    except Exception as e:
        print(f"Error sending reminder to {user_id}: {e}")

def add_reminder_job(user_id: int, title: str, reminder_id: int, remind_time, bot):
    """افزودن یادآوری به scheduler"""
    scheduler.add_job(
        send_reminder,
        DateTrigger(run_date=remind_time),
        args=[user_id, title, reminder_id, config.BOT_TOKEN],
        id=f"reminder_{reminder_id}"
    )

def start_scheduler():
    """استارت scheduler"""
    scheduler.add_job(send_morning_messages, 'cron', hour=7, minute=0, id="morning_job")
    scheduler.add_job(send_night_messages, 'cron', hour=23, minute=0, id="night_job")
    scheduler.add_job(check_absent_users, 'cron', hour=10, minute=0, id="absent_job")
    scheduler.start()
    print("✅ Scheduler started successfully!")
