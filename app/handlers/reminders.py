from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.database import SessionLocal
from app.models import Reminder
from datetime import datetime
import pytz
import re

DATE, TIME, TITLE = range(3, 6)

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 **تنظیم یادآوری - مرحله ۱ از ۳**\n\n"
        "لطفاً تاریخ را به فرمت `YYYY-MM-DD` وارد کنید.\n"
        "مثال: `2025-12-25`"
    )
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        date_str = update.message.text.strip()
        datetime.strptime(date_str, "%Y-%m-%d")
        context.user_data['reminder_date'] = date_str
        await update.message.delete()
        await update.message.reply_text(
            "⏰ **مرحله ۲ از ۳**\n\n"
            "لطفاً ساعت را به فرمت `HH:MM` وارد کنید.\n"
            "مثال: `14:30`"
        )
        return TIME
    except:
        await update.message.reply_text(
            "❌ فرمت تاریخ اشتباه است!\n"
            "لطفاً به فرمت `YYYY-MM-DD` وارد کنید.\n"
            "مثال: `2025-12-25`"
        )
        return DATE

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        time_str = update.message.text.strip()
        datetime.strptime(time_str, "%H:%M")
        context.user_data['reminder_time'] = time_str
        await update.message.delete()
        await update.message.reply_text(
            "📝 **مرحله ۳ از ۳**\n\n"
            "لطفاً عنوان یادآوری را وارد کنید:"
        )
        return TITLE
    except:
        await update.message.reply_text(
            "❌ فرمت ساعت اشتباه است!\n"
            "لطفاً به فرمت `HH:MM` وارد کنید.\n"
            "مثال: `14:30`"
        )
        return TIME

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    context.user_data['reminder_title'] = title
    await update.message.delete()
    
    # ترکیب تاریخ و ساعت
    date_str = context.user_data['reminder_date']
    time_str = context.user_data['reminder_time']
    datetime_str = f"{date_str} {time_str}"
    
    try:
        remind_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        remind_time = pytz.timezone("Asia/Tehran").localize(remind_time)
        
        now = datetime.now(pytz.timezone("Asia/Tehran"))
        if remind_time < now:
            await update.message.reply_text("❌ زمان وارد شده گذشته است!")
            return ConversationHandler.END
        
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
        
        # اضافه کردن به scheduler
        from app.scheduler import add_reminder_job
        add_reminder_job(update.effective_user.id, title, reminder_id, remind_time, update.get_bot())
        
        await update.message.reply_text(
            f"✅ **یادآوری تنظیم شد!**\n\n"
            f"📌 عنوان: {title}\n"
            f"⏰ زمان: {datetime_str}\n"
            f"🆔 شناسه: {reminder_id}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    
    return ConversationHandler.END

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست یادآوری‌های فعال"""
    user_id = update.effective_user.id
    db = SessionLocal()
    reminders = db.query(Reminder).filter_by(user_id=user_id, is_active=True).all()
    db.close()
    
    if not reminders:
        await update.message.reply_text("📭 **هیچ یادآوری فعالی ندارید!**")
        return
    
    text = "📋 **لیست یادآوری‌های فعال:**\n\n"
    for i, r in enumerate(reminders[:10], 1):
        time_str = r.remind_time.strftime("%Y-%m-%d %H:%M")
        text += f"{i}. {r.title}\n   ⏰ {time_str}\n   🆔 شناسه: `{r.id}`\n\n"
    
    text += "برای لغو یادآوری: /cancel_reminder [شناسه]"
    await update.message.reply_text(text)

async def cancel_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو یک یادآوری با شناسه"""
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ لطفاً شناسه یادآوری را وارد کنید.\n"
                "مثال: /cancel_reminder 5"
            )
            return
        
        reminder_id = int(context.args[0])
        user_id = update.effective_user.id
        
        db = SessionLocal()
        reminder = db.query(Reminder).filter_by(id=reminder_id, user_id=user_id).first()
        
        if reminder:
            reminder.is_active = False
            db.commit()
            await update.message.reply_text(f"✅ **یادآوری با شناسه {reminder_id} لغو شد.**")
        else:
            await update.message.reply_text(f"❌ یادآوری با شناسه {reminder_id} پیدا نشد.")
        db.close()
        
    except ValueError:
        await update.message.reply_text("❌ شناسه باید یک عدد باشد.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
