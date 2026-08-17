from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from app.config import config
from app.database import SessionLocal
from app.models import User
from app.data.health_messages import HEALTH_MESSAGES
from app.messages import get_morning_message, get_night_message, get_absent_message
from datetime import datetime, timedelta
import pytz
import logging
import asyncio

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tehran"))

async def send_morning_messages():
    """ارسال پیام صبح بخیر + انگیزشی (دو پیام جداگانه)"""
    try:
        bot = Bot(token=config.BOT_TOKEN)
        db = SessionLocal()
        users = db.query(User).filter_by(morning_msg_enabled=True, is_active=True).all()
        
        logger.info(f"ارسال پیام صبح به {len(users)} کاربر")
        
        for user in users:
            try:
                # ۱. پیام سلامتی
                sent = user.sent_health_messages or []
                if sent:
                    last_day = max([m.get("day", 0) for m in sent])
                    next_day = (last_day % 30) + 1
                else:
                    next_day = 1
                
                health_data = HEALTH_MESSAGES[next_day - 1]
                
                health_text = (
                    f"🌅 **صبح بخیر {user.preferred_name}!**\n\n"
                    f"📌 **روز {next_day} از ۳۰**\n"
                    f"**{health_data['title']}**\n\n"
                    f"{health_data['message']}\n\n"
                    f"💪 برای سلامتی‌ات ارزش قائل شو!"
                )
                
                # ارسال پیام سلامتی با دکمه بازگشت به منو
                keyboard = [[InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]]
                await bot.send_message(
                    chat_id=user.user_id,
                    text=health_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                # ذخیره تاریخچه
                sent.append({
                    "date": datetime.now().isoformat(),
                    "day": next_day,
                    "title": health_data['title'],
                    "message": health_data['message']
                })
                user.sent_health_messages = sent
                db.commit()
                
                # ۲. پیام انگیزشی (جداگانه)
                motivational_text = get_morning_message(user.gender)
                motivational_text = f"✨ **یادآوری امروز:**\n\n{motivational_text}"
                
                # پیام انگیزشی بدون دکمه (برای زیبایی)
                await bot.send_message(
                    chat_id=user.user_id,
                    text=motivational_text
                )
                
                logger.info(f"پیام‌های صبح به {user.user_id} ارسال شد")
                
            except Exception as e:
                logger.error(f"خطا در ارسال به {user.user_id}: {e}")
        
        db.close()
        logger.info("ارسال پیام صبح تکمیل شد")
        
    except Exception as e:
        logger.error(f"خطا در send_morning_messages: {e}")

async def send_night_messages():
    """ارسال پیام شب بخیر + پرسش احساسات با دکمه بازگشت به منو"""
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
                    ],
                    [InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]
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
                    f"{get_absent_message()}\n\n"
                    f"هر وقت خواستی برگرد، منتظرتم. 💙"
                )
                keyboard = [[InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]]
                await bot.send_message(
                    chat_id=user.user_id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
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
