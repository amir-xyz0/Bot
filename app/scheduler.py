import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.database import SessionLocal
from app.models import User
from app.messages import (
    get_morning_message,
    get_night_message,
    get_random_motivational,
    get_random_health_message,
    MOOD_REQUEST_MESSAGE
)

logger = logging.getLogger(__name__)

_application = None

def set_application(app):
    global _application
    _application = app
    logger.info("✅ Application در Scheduler ذخیره شد.")

async def send_message_to_user(user_id, text, reply_markup=None):
    global _application
    if not _application:
        logger.error("❌ Application در دسترس نیست!")
        return False
    try:
        await _application.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup
        )
        logger.info(f"✅ پیام به کاربر {user_id} ارسال شد")
        return True
    except Exception as e:
        logger.error(f"❌ خطا در ارسال پیام به {user_id}: {e}")
        return False

async def send_morning_messages():
    """ارسال ۳ پیام صبحگاهی + دکمه بازگشت در پیام آخر (بدون حذف پیام)"""
    logger.info(f"🌅 شروع ارسال پیام‌های صبحگاهی در ساعت {datetime.now().strftime('%H:%M')}")
    
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.morning_msg_enabled == True,
            User.notifications == True
        ).all()
        
        logger.info(f"📊 تعداد کاربران با اعلان صبح فعال: {len(users)}")
        
        if not users:
            logger.info("⏭️ هیچ کاربری با اعلان صبح فعال وجود ندارد.")
            return
        
        for user in users:
            try:
                # ۱. پیام صبح بخیر
                await send_message_to_user(user.user_id, get_morning_message(user.preferred_name or 'عزیز'))
                
                # ۲. پیام انگیزشی (با تأخیر ۳ ثانیه)
                await asyncio.sleep(3)
                await send_message_to_user(user.user_id, get_random_motivational())
                
                # ۳. پیام سلامت + دکمه بازگشت (با تأخیر ۳ ثانیه)
                await asyncio.sleep(3)
                health_text = get_random_health_message()
                
                # 🔥 دکمه بازگشت با callback_data جدید (برای جلوگیری از حذف پیام)
                keyboard = [[InlineKeyboardButton("🏠 بازگشت به خانه", callback_data="main_menu_keep")]]
                
                await send_message_to_user(
                    user.user_id,
                    health_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                logger.info(f"✅ ۳ پیام صبحگاهی به کاربر {user.user_id} ارسال شد")
            except Exception as e:
                logger.error(f"❌ خطا در ارسال به کاربر {user.user_id}: {e}")
            
    except Exception as e:
        logger.error(f"❌ خطا در ارسال پیام‌های صبحگاهی: {e}")
    finally:
        db.close()
    
    logger.info("✅ ارسال پیام‌های صبحگاهی به پایان رسید.")

async def send_night_messages():
    """ارسال ۲ پیام شبانه به کاربران فعال"""
    logger.info(f"🌙 شروع ارسال پیام‌های شبانه در ساعت {datetime.now().strftime('%H:%M')}")
    
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.night_msg_enabled == True,
            User.notifications == True
        ).all()
        
        logger.info(f"📊 تعداد کاربران با اعلان شب فعال: {len(users)}")
        
        if not users:
            logger.info("⏭️ هیچ کاربری با اعلان شب فعال وجود ندارد.")
            return
        
        for user in users:
            try:
                # ۱. پیام شب بخیر
                await send_message_to_user(user.user_id, get_night_message(user.preferred_name or 'عزیز'))
                
                # ۲. پیام ثبت احساسات با دکمه (با تأخیر ۳ ثانیه)
                await asyncio.sleep(3)
                keyboard = [
                    [InlineKeyboardButton("😊 خوب", callback_data="mood_good")],
                    [InlineKeyboardButton("😐 معمولی", callback_data="mood_neutral")],
                    [InlineKeyboardButton("😔 بد", callback_data="mood_bad")]
                ]
                await send_message_to_user(
                    user.user_id,
                    MOOD_REQUEST_MESSAGE,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                logger.info(f"✅ ۲ پیام شبانه به کاربر {user.user_id} ارسال شد")
            except Exception as e:
                logger.error(f"❌ خطا در ارسال به کاربر {user.user_id}: {e}")
            
    except Exception as e:
        logger.error(f"❌ خطا در ارسال پیام‌های شبانه: {e}")
    finally:
        db.close()
    
    logger.info("✅ ارسال پیام‌های شبانه به پایان رسید.")

def start_scheduler(app):
    global _application
    _application = app
    logger.info("⏰ در حال راه‌اندازی Scheduler...")
    
    scheduler = AsyncIOScheduler(timezone="Asia/Tehran")
    
    scheduler.add_job(
        send_morning_messages,
        CronTrigger(hour=23, minute=19),
        id="morning_job",
        replace_existing=True
    )
    logger.info("✅ job صبحگاهی تنظیم شد (ساعت ۷:۰۰ به وقت تهران)")
    
    scheduler.add_job(
        send_night_messages,
        CronTrigger(hour=23, minute=43),
        id="night_job",
        replace_existing=True
    )
    logger.info("✅ job شبانه تنظیم شد (ساعت ۲۳:۰۰ به وقت تهران)")
    
    scheduler.start()
    logger.info("🚀 Scheduler با موفقیت راه‌اندازی شد!")
    
    jobs = scheduler.get_jobs()
    logger.info(f"📋 Jobهای فعال: {[job.id for job in jobs]}")
    
    return scheduler
