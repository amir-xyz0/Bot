from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from app.config import config
from app.database import SessionLocal
from app.models import User
from app.data.health_messages import HEALTH_MESSAGES
from datetime import datetime, timedelta
import pytz
import logging
import asyncio

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tehran"))

async def send_morning_messages():
    try:
        bot = Bot(token=config.BOT_TOKEN)
        db = SessionLocal()
        users = db.query(User).filter_by(health_msg_enabled=True, is_active=True).all()
        
        logger.info(f"ارسال پیام صبح به {len(users)} کاربر")
        
        for user in users:
            try:
                sent = user.sent_health_messages or []
                if sent:
                    last_day = max([m.get("day", 0) for m in sent])
                    next_day = (last_day % 30) + 1
                else:
                    next_day = 1
                
                message_data = HEALTH_MESSAGES[next_day - 1]
                
                text = (
                    f"🌅 **صبح بخیر {user.preferred_name}!**\n\n"
                    f"📌 **روز {next_day} از ۳۰**\n"
                    f"**{message_data['title']}**\n\n"
                    f"{message_data['message']}\n\n"
                    f"💪 برای سلامتی‌ات ارزش قائل شو!"
                )
                await bot.send_message(chat_id=user.user_id, text=text)
                
                sent.append({
                    "date": datetime.now().isoformat(),
                    "day": next_day,
                    "title": message_data['title'],
                    "message": message_data['message']
                })
                user.sent_health_messages = sent
                db.commit()
                logger.info(f"پیام صبح به {user.user_id} ارسال شد")
                
            except Exception as e:
                logger.error(f"خطا در ارسال به {user.user_id}: {e}")
        
        db.close()
        logger.info("ارسال پیام صبح تکمیل شد")
        
    except Exception as e:
        logger.error(f"خطا در send_morning_messages: {e}")

async def send_night_messages():
    try:
        bot = Bot(token=config.BOT_TOKEN)
        db = SessionLocal()
        users = db.query(User).filter_by(night_msg_enabled=True, is_active=True).all()
        
        logger.info(f"ارسال پیام شب به {len(users)} کاربر")
        
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
                    f"روزت چطور بود؟\n"
                    f"با انتخاب یکی از گزینه‌ها، احساس امروزت رو ثبت کن."
                )
                await bot.send_message(
                    chat_id=user.user_id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                logger.info(f"پیام شب به {user.user_id} ارسال شد")
                
            except Exception as e:
                logger.error(f"خطا در ارسال به {user.user_id}: {e}")
        
        db.close()
        logger.info("ارسال پیام شب تکمیل شد")
        
    except Exception as e:
        logger.error(f"خطا در send_night_messages: {e}")

async def check_absent_users():
    try:
        bot = Bot(token=config.BOT_TOKEN)
        db = SessionLocal()
        three_days_ago = datetime.now(pytz.timezone("Asia/Tehran")) - timedelta(days=3)
        users = db.query(User).filter(User.last_activity < three_days_ago).all()
        
        logger.info(f"ارسال پیام غیبت به {len(users)} کاربر")
        
        for user in users:
            try:
                text = (
                    f"👋 **سلام {user.preferred_name}!**\n\n"
                    f"چند روزی نبودی، نگرانت شدم.\n"
                    f"امیدوارم حالت خوب باشه. هر وقت خواستی برگرد، منتظرتم. 💙"
                )
                await bot.send_message(chat_id=user.user_id, text=text)
                logger.info(f"پیام غیبت به {user.user_id} ارسال شد")
            except Exception as e:
                logger.error(f"خطا در ارسال به {user.user_id}: {e}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"خطا در check_absent_users: {e}")

def start_scheduler():
    try:
        scheduler.remove_all_jobs()
        
        scheduler.add_job(
            send_morning_messages,
            CronTrigger(hour=7, minute=0, timezone=pytz.timezone("Asia/Tehran")),
            id="morning_job"
        )
        scheduler.add_job(
            send_night_messages,
            CronTrigger(hour=23, minute=0, timezone=pytz.timezone("Asia/Tehran")),
            id="night_job"
        )
        scheduler.add_job(
            check_absent_users,
            CronTrigger(hour=10, minute=0, timezone=pytz.timezone("Asia/Tehran")),
            id="absent_job"
        )
        
        scheduler.start()
        logger.info("✅ Scheduler با موفقیت راه‌اندازی شد!")
        logger.info(f"Jobs: {[j.id for j in scheduler.get_jobs()]}")
        
    except Exception as e:
        logger.error(f"❌ خطا در start_scheduler: {e}")
