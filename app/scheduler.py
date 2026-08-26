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

# ============================================================
# متغیر سراسری برای دسترسی به Application
# ============================================================
_application = None

def set_application(app):
    """ذخیره Application برای استفاده در jobها"""
    global _application
    _application = app
    logger.info("✅ Application در Scheduler ذخیره شد.")

# ============================================================
# تابع اصلی ارسال پیام با مدیریت خطا
# ============================================================
async def send_message_to_user(user_id, text, reply_markup=None):
    """ارسال پیام به کاربر با مدیریت کامل خطا"""
    global _application
    
    if not _application:
        logger.error("❌ Application در دسترس نیست! پیام ارسال نشد.")
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

# ============================================================
# ارسال پیام‌های صبحگاهی (ساعت ۷ صبح)
# ============================================================
async def send_morning_messages():
    """ارسال ۳ پیام صبحگاهی به کاربران فعال"""
    logger.info(f"🌅 شروع ارسال پیام‌های صبحگاهی در ساعت {datetime.now().strftime('%H:%M')}")
    
    db = SessionLocal()
    try:
        # دریافت کاربرانی که اعلان صبح فعال دارند
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
                
                # ۳. پیام سلامت (با تأخیر ۳ ثانیه)
                await asyncio.sleep(3)
                await send_message_to_user(user.user_id, get_random_health_message())
                
                logger.info(f"✅ ۳ پیام صبحگاهی به کاربر {user.user_id} ارسال شد")
            except Exception as e:
                logger.error(f"❌ خطا در ارسال به کاربر {user.user_id}: {e}")
            
    except Exception as e:
        logger.error(f"❌ خطا در ارسال پیام‌های صبحگاهی: {e}")
    finally:
        db.close()
    
    logger.info("✅ ارسال پیام‌های صبحگاهی به پایان رسید.")

# ============================================================
# ارسال پیام‌های شبانه (ساعت ۲۳)
# ============================================================
async def send_night_messages():
    """ارسال ۲ پیام شبانه به کاربران فعال"""
    logger.info(f"🌙 شروع ارسال پیام‌های شبانه در ساعت {datetime.now().strftime('%H:%M')}")
    
    db = SessionLocal()
    try:
        # دریافت کاربرانی که اعلان شب فعال دارند
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

# ============================================================
# راه‌اندازی Scheduler
# ============================================================
def start_scheduler(app):
    """راه‌اندازی Scheduler با زمان تهران"""
    global _application
    _application = app
    logger.info("⏰ در حال راه‌اندازی Scheduler...")
    
    # ایجاد Scheduler با منطقه زمانی تهران
    scheduler = AsyncIOScheduler(timezone="Asia/Tehran")
    
    # اضافه کردن job صبح (ساعت ۷)
    scheduler.add_job(
        send_morning_messages,
        CronTrigger(hour=12, minute=20),
        id="morning_job",
        replace_existing=True
    )
    logger.info("✅ job صبحگاهی تنظیم شد (ساعت ۷:۰۰ به وقت تهران)")
    
    # اضافه کردن job شب (ساعت ۲۳)
    scheduler.add_job(
        send_night_messages,
        CronTrigger(hour=23, minute=0),
        id="night_job",
        replace_existing=True
    )
    logger.info("✅ job شبانه تنظیم شد (ساعت ۲۳:۰۰ به وقت تهران)")
    
    # شروع Scheduler
    scheduler.start()
    logger.info("🚀 Scheduler با موفقیت راه‌اندازی شد!")
    
    # نمایش jobهای فعال
    jobs = scheduler.get_jobs()
    logger.info(f"📋 Jobهای فعال: {[job.id for job in jobs]}")
    
    return scheduler
