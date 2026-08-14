import pytz
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from app.database import SessionLocal
from app.models import Reminder
from app.utils.helpers import get_tehran_time

# تنظیم لاگر
logger = logging.getLogger(__name__)

# ایجاد نمونه Scheduler (در سطح ماژول)
scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Tehran"))

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به حالت تنظیم یادآوری"""
    await update.message.reply_text(
        "⏰ **تنظیم یادآوری**\n\n"
        "لطفاً زمان و متن رو به این شکل وارد کن:\n"
        "`2025-01-15 14:30 | جلسه با آقای کریمی`\n\n"
        "برای لغو /cancel رو بزن."
    )

async def process_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش یادآوری وارد شده توسط کاربر"""
    try:
        parts = update.message.text.split("|")
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ فرمت وارد شده صحیح نیست!\n"
                "فرمت صحیح: `2025-01-15 14:30 | عنوان یادآوری`"
            )
            return
        
        time_str = parts[0].strip()
        title = parts[1].strip()
        
        remind_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        remind_time = pytz.timezone("Asia/Tehran").localize(remind_time)
        
        if remind_time < get_tehran_time():
            await update.message.reply_text("❌ زمان وارد شده گذشته! لطفاً زمان آینده رو وارد کن.")
            return
        
        # ذخیره در دیتابیس
        db = SessionLocal()
        reminder = Reminder(
            user_id=update.effective_user.id,
            title=title,
            description=f"یادآوری: {title}",
            remind_time=remind_time,
            is_active=True
        )
        db.add(reminder)
        db.commit()
        reminder_id = reminder.id
        db.close()
        
        # اضافه کردن job به scheduler
        scheduler.add_job(
            send_reminder,
            DateTrigger(run_date=remind_time),
            args=[update.effective_user.id, title, reminder_id, update.get_bot()]
        )
        
        await update.message.reply_text(
            f"✅ یادآوری برای {time_str} با عنوان «{title}» تنظیم شد!"
        )
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ خطا در فرمت زمان!\n"
            f"فرمت صحیح: `2025-01-15 14:30 | عنوان`\n"
            f"جزئیات: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in process_reminder: {e}")
        await update.message.reply_text(f"❌ مشکلی پیش اومد: {str(e)}")

async def send_reminder(user_id: int, title: str, reminder_id: int, bot):
    """ارسال پیام یادآوری به کاربر (این تابع توسط scheduler اجرا میشه)"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"⏰ **یادآوری!**\n\n{title}\n\nزمانش رسیده! 🕐"
        )
        
        # غیرفعال کردن یادآوری در دیتابیس
        db = SessionLocal()
        reminder = db.query(Reminder).filter_by(id=reminder_id).first()
        if reminder:
            reminder.is_active = False
            db.commit()
        db.close()
        
    except Exception as e:
        logger.error(f"Error sending reminder to {user_id}: {e}")

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست یادآوری‌های فعال"""
    user_id = update.effective_user.id
    db = SessionLocal()
    reminders = db.query(Reminder).filter_by(user_id=user_id, is_active=True).all()
    db.close()
    
    if not reminders:
        await update.message.reply_text("📭 هیچ یادآوری فعالی نداری!")
        return
    
    text = "📋 **یادآوری‌های فعال:**\n\n"
    for i, r in enumerate(reminders[:10], 1):
        time_str = r.remind_time.strftime("%Y-%m-%d %H:%M")
        text += f"{i}. {r.title} - {time_str}\n"
    
    await update.message.reply_text(text)

async def cancel_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو یک یادآوری با شناسه"""
    try:
        if not context.args or len(context.args) == 0:
            await update.message.reply_text(
                "❌ لطفاً شناسه یادآوری رو وارد کن.\n"
                "مثال: `/cancel_reminder 5`"
            )
            return
        
        reminder_id = int(context.args[0])
        user_id = update.effective_user.id
        
        db = SessionLocal()
        reminder = db.query(Reminder).filter_by(id=reminder_id, user_id=user_id).first()
        
        if reminder:
            reminder.is_active = False
            db.commit()
            await update.message.reply_text(f"✅ یادآوری با شناسه {reminder_id} لغو شد.")
        else:
            await update.message.reply_text(f"❌ یادآوری با شناسه {reminder_id} پیدا نشد.")
        db.close()
        
    except ValueError:
        await update.message.reply_text("❌ شناسه باید یک عدد باشه.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

def schedule_existing_reminders():
    """زمان‌بندی مجدد یادآوری‌های فعال از دیتابیس (در هنگام راه‌اندازی)"""
    db = SessionLocal()
    reminders = db.query(Reminder).filter_by(is_active=True).all()
    now = get_tehran_time()
    
    for r in reminders:
        if r.remind_time > now:
            # اینجا برای ارسال نیاز به bot داریم که در main.py باید پاس داده بشه
            # فعلاً فقط لاگ می‌کنیم
            logger.info(f"Scheduled reminder: {r.title} at {r.remind_time}")
    
    db.close()
