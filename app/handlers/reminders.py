from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import Reminder
from datetime import datetime
import pytz
import re

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏰ **تنظیم یادآوری**\n\n"
        "لطفاً زمان و متن را به این شکل وارد کنید:\n"
        "`2025-01-15 14:30 | جلسه با آقای کریمی`\n\n"
        "برای لغو، /cancel را بزنید."
    )

async def process_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        parts = text.split("|")
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ فرمت صحیح نیست!\n"
                "فرمت صحیح: `2025-01-15 14:30 | عنوان یادآوری`"
            )
            return
        
        time_str = parts[0].strip()
        title = parts[1].strip()
        
        # بررسی فرمت زمان
        try:
            remind_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            remind_time = pytz.timezone("Asia/Tehran").localize(remind_time)
        except:
            await update.message.reply_text(
                "❌ فرمت زمان اشتباه است!\n"
                "فرمت صحیح: `2025-01-15 14:30`"
            )
            return
        
        now = datetime.now(pytz.timezone("Asia/Tehran"))
        if remind_time < now:
            await update.message.reply_text("❌ زمان وارد شده گذشته است!")
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
        
        # اضافه کردن به scheduler
        from app.scheduler import add_reminder_job
        add_reminder_job(update.effective_user.id, title, reminder_id, remind_time, update.get_bot())
        
        await update.message.reply_text(
            f"✅ **یادآوری تنظیم شد!**\n\n"
            f"📌 عنوان: {title}\n"
            f"⏰ زمان: {time_str}\n"
            f"🆔 شناسه: {reminder_id}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        text += f"{i}. {r.title}\n   ⏰ {time_str}\n   🆔 شناسه: {r.id}\n\n"
    
    text += "برای لغو یادآوری: /cancel_reminder [شناسه]"
    await update.message.reply_text(text)

async def cancel_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
