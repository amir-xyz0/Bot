from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from app.database import SessionLocal
from app.models import Reminder
from app.utils.helpers import get_tehran_time
import pytz

scheduler = AsyncIOScheduler()

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏰ **تنظیم یادآوری**\n\n"
        "لطفاً زمان و متن رو به این شکل وارد کن:\n"
        "`2025-01-15 14:30 | جلسه با آقای کریمی`\n\n"
        "برای لغو /cancel رو بزن."
    )

async def process_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split("|")
        time_str = parts[0].strip()
        title = parts[1].strip()
        
        remind_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        remind_time = pytz.timezone("Asia/Tehran").localize(remind_time)
        
        if remind_time < get_tehran_time():
            await update.message.reply_text("❌ زمان وارد شده گذشته! لطفاً زمان آینده رو وارد کن.")
            return
        
        db = SessionLocal()
        reminder = Reminder(
            user_id=update.effective_user.id,
            title=title,
            description=f"یادآوری: {title}",
            remind_time=remind_time
        )
        db.add(reminder)
        db.commit()
        reminder_id = reminder.id
        db.close()
        
        scheduler.add_job(
            send_reminder,
            DateTrigger(run_date=remind_time),
            args=[update.effective_user.id, title, reminder_id]
        )
        
        await update.message.reply_text(f"✅ یادآوری برای {time_str} با عنوان «{title}» تنظیم شد!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}\nفرمت صحیح: `2025-01-15 14:30 | عنوان`")

async def send_reminder(user_id: int, title: str, reminder_id: int):
    # این تابع توسط scheduler اجرا میشه
    try:
        # باید context رو از جای دیگه بگیریم - اینجا یه نمونه سادست
        # در نسخه کامل باید از bot instance استفاده کنی
        pass
    except Exception as e:
        print(f"Error sending reminder: {e}")

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
