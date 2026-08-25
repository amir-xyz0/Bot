import logging
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

# ذخیره context برای دسترسی به bot
_bot_context = None

def set_bot_context(context):
    """ذخیره context برای استفاده در jobها"""
    global _bot_context
    _bot_context = context

async def send_message_to_user(user_id, text):
    """ارسال پیام به کاربر با مدیریت خطا"""
    global _bot_context
    if not _bot_context:
        logger.error("❌ context ربات در دسترس نیست!")
        return False
    
    try:
        await _bot_context.bot.send_message(chat_id=user_id, text=text)
        logger.info(f"✅ پیام به کاربر {user_id} ارسال شد")
        return True
    except Exception as e:
        logger.error(f"❌ خطا در ارسال پیام به {user_id}: {e}")
        return False

async def send_morning_messages():
    """ارسال پیام صبحگاهی به کاربران"""
    logger.info("🌅 شروع ارسال پیام‌های صبحگاهی...")
    
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.morning_msg_enabled == True,
            User.notifications == True
        ).all()
        
        logger.info(f"📊 تعداد کاربران با اعلان صبح فعال: {len(users)}")
        
        for user in users:
            text = (
                f"🌅 **صبح بخیر {user.preferred_name}!**\n\n"
                "امروز روز جدیدیه، پر از فرصت‌های تازه.\n"
                "🌸 امیدوارم روزی پر از آرامش و لحظات خوب داشته باشی.\n\n"
                "✨ یادت باشه: هر روز یه شروع تازه‌ست."
            )
            await send_message_to_user(user.user_id, text)
            
    except Exception as e:
        logger.error(f"❌ خطا در ارسال پیام‌های صبحگاهی: {e}")
    finally:
        db.close()
    
    logger.info("✅ ارسال پیام‌های صبحگاهی به پایان رسید.")

async def send_night_messages():
    """ارسال پیام شبانه به کاربران"""
    logger.info("🌙 شروع ارسال پیام‌های شبانه...")
    
    db = SessionLocal()
    try:
        # فقط کاربرانی که اعلان شب فعال دارند
        users = db.query(User).filter(
            User.night_msg_enabled == True,
            User.notifications == True
        ).all()
        
        logger.info(f"📊 تعداد کاربران با اعلان شب فعال: {len(users)}")
        
        for user in users:
            text = (
                f"🌙 **شب بخیر {user.preferred_name}!**\n\n"
                "روزت چطور بود؟ امیدوارم لحظات خوبی داشته باشی.\n"
                "🌟 فردا روز جدیدیه، پس آروم بگیر و به خودت استراحت بده.\n\n"
                "💭 یادت باشه: هر شب پایان یه روز و شروع یه رویاست."
            )
            await send_message_to_user(user.user_id, text)
            
    except Exception as e:
        logger.error(f"❌ خطا در ارسال پیام‌های شبانه: {e}")
    finally:
        db.close()
    
    logger.info("✅ ارسال پیام‌های شبانه به پایان رسید.")

async def check_absent_users():
    """بررسی کاربرانی که مدت‌هست احساسات ثبت نکردن"""
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
    
    # پیام صبح: ساعت ۸ صبح
    scheduler.add_job(
        send_morning_messages,
        CronTrigger(hour=8, minute=0),
        id="morning_job",
        replace_existing=True
    )
    logger.info("✅ job صبحگاهی تنظیم شد (ساعت ۸:۰۰)")
    
    # پیام شب: ساعت ۱۰ شب
    scheduler.add_job(
        send_night_messages,
        CronTrigger(hour=23, minute=0),
        id="night_job",
        replace_existing=True
    )
    logger.info("✅ job شبانه تنظیم شد (ساعت ۲۳:۰۰)")
    
    # بررسی کاربران غایب: هر روز ساعت ۱۲ ظهر
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
