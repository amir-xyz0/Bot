import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
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

_bot_context = None

def set_bot_context(context):
    global _bot_context
    _bot_context = context

async def send_message_to_user(user_id, text, reply_markup=None):
    global _bot_context
    if not _bot_context:
        logger.error("❌ context ربات در دسترس نیست!")
        return False
    try:
        await _bot_context.bot.send_message(
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
    """ارسال پیام صبح (ساعت ۷) + پیام انگیزشی رندم + پیام سلامت رندم"""
    logger.info("🌅 شروع ارسال پیام‌های صبحگاهی...")
    
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.morning_msg_enabled == True,
            User.notifications == True
        ).all()
        
        logger.info(f"📊 تعداد کاربران با اعلان صبح فعال: {len(users)}")
        
        for user in users:
            # ۱. پیام صبح بخیر
            morning_text = get_morning_message(user.preferred_name or 'عزیز')
            await send_message_to_user(user.user_id, morning_text)
            
            # ۲. پیام انگیزشی رندم (با تأخیر ۵ ثانیه)
            await asyncio.sleep(5)
            motivational_text = get_random_motivational()
            await send_message_to_user(user.user_id, motivational_text)
            
            # ۳. پیام سلامت رندم (با تأخیر ۵ ثانیه)
            await asyncio.sleep(5)
            health_text = get_random_health_message()
            await send_message_to_user(user.user_id, health_text)
            
            logger.info(f"✅ ۳ پیام صبحگاهی به کاربر {user.user_id} ارسال شد")
            
    except Exception as e:
        logger.error(f"❌ خطا در ارسال پیام‌های صبحگاهی: {e}")
    finally:
        db.close()
    
    logger.info("✅ ارسال پیام‌های صبحگاهی به پایان رسید.")

async def send_night_messages():
    """ارسال پیام شب (ساعت ۲۳) + پیام ثبت احساسات با دکمه"""
    logger.info("🌙 شروع ارسال پیام‌های شبانه...")
    
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.night_msg_enabled == True,
            User.notifications == True
        ).all()
        
        logger.info(f"📊 تعداد کاربران با اعلان شب فعال: {len(users)}")
        
        for user in users:
            # ۱. پیام شب بخیر
            night_text = get_night_message(user.preferred_name or 'عزیز')
            await send_message_to_user(user.user_id, night_text)
            
            # ۲. پیام ثبت احساسات با دکمه‌ها (با تأخیر ۵ ثانیه)
            await asyncio.sleep(5)
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
        logger.error(f"❌ خطا در ارسال پیام‌های شبانه: {e}")
    finally:
        db.close()
    
    logger.info("✅ ارسال پیام‌های شبانه به پایان رسید.")

async def check_absent_users():
    """بررسی کاربران غایب"""
    logger.info("🔍 شروع بررسی کاربران غایب...")
    db = SessionLocal()
    try:
        users = db.query(User).all()
        logger.info(f"📊 تعداد کل کاربران: {len(users)}")
    except Exception as e:
        logger.error(f"❌ خطا در بررسی کاربران غایب: {e}")
    finally:
        db.close()
    logger.info("✅ بررسی کاربران غایب به پایان رسید.")

def start_scheduler(app=None):
    """راه‌اندازی Scheduler"""
    logger.info("⏰ در حال راه‌اندازی Scheduler...")
    
    if app:
        set_bot_context(app)
        logger.info("✅ context ربات تنظیم شد.")
    
    scheduler = BackgroundScheduler()
    
    # پیام صبح: ساعت ۷ صبح
    scheduler.add_job(
        send_morning_messages,
        CronTrigger(hour=7, minute=0),
        id="morning_job",
        replace_existing=True
    )
    logger.info("✅ job صبحگاهی تنظیم شد (ساعت ۷:۰۰)")
    
    # پیام شب: ساعت ۲۳
    scheduler.add_job(
        send_night_messages,
        CronTrigger(hour=23, minute=0),
        id="night_job",
        replace_existing=True
    )
    logger.info("✅ job شبانه تنظیم شد (ساعت ۲۳:۰۰)")
    
    # بررسی کاربران غایب: ساعت ۱۲
    scheduler.add_job(
        check_absent_users,
        CronTrigger(hour=12, minute=0),
        id="absent_job",
        replace_existing=True
    )
    logger.info("✅ job بررسی غایب‌ها تنظیم شد (ساعت ۱۲:۰۰)")
    
    scheduler.start()
    logger.info("🚀 Scheduler با موفقیت راه‌اندازی شد!")
    
    jobs = scheduler.get_jobs()
    logger.info(f"📋 Jobهای فعال: {[job.id for job in jobs]}")
    
    return scheduler
