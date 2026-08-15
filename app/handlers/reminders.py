from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.database import SessionLocal
from app.models import Reminder
from datetime import datetime, timedelta
import pytz
import calendar

DATE, TIME, TITLE = range(3, 6)

# تاریخ‌های پیشنهادی
QUICK_DATES = [
    ("امروز", 0),
    ("فردا", 1),
    ("۳ روز بعد", 3),
    ("۵ روز بعد", 5),
    ("۱ هفته بعد", 7),
]

# ساعت‌های پیشنهادی
QUICK_TIMES = [
    ("۸ صبح", "08:00"),
    ("۱۰ صبح", "10:00"),
    ("۱۲ ظهر", "12:00"),
    ("۲ بعدازظهر", "14:00"),
    ("۴ بعدازظهر", "16:00"),
    ("۶ عصر", "18:00"),
    ("۸ شب", "20:00"),
]

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع تنظیم یادآوری با دکمه‌های تاریخ"""
    keyboard = []
    row = []
    for i, (label, days) in enumerate(QUICK_DATES):
        row.append(InlineKeyboardButton(label, callback_data=f"date_{days}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📅 انتخاب دستی", callback_data="date_manual")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")])
    
    await update.message.reply_text(
        "📅 **تنظیم یادآوری - مرحله ۱ از ۳**\n\n"
        "لطفاً تاریخ مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return DATE

async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش انتخاب تاریخ"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.replace("date_", "")
    
    if data == "manual":
        await query.edit_message_text(
            "📅 **تاریخ را به فرمت `YYYY-MM-DD` وارد کنید**\n"
            "مثال: `2025-12-25`"
        )
        return DATE
    
    days = int(data)
    selected_date = datetime.now(pytz.timezone("Asia/Tehran")) + timedelta(days=days)
    context.user_data['reminder_date'] = selected_date.strftime("%Y-%m-%d")
    
    # رفتن به مرحله انتخاب ساعت
    return await show_time_selection(update, context)

async def show_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش دکمه‌های ساعت"""
    keyboard = []
    row = []
    for label, time in QUICK_TIMES:
        row.append(InlineKeyboardButton(label, callback_data=f"time_{time}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⏰ انتخاب دستی", callback_data="time_manual")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به تاریخ", callback_data="back_to_date")])
    
    if hasattr(update, 'callback_query'):
        await update.callback_query.edit_message_text(
            f"📅 تاریخ انتخاب‌شده: `{context.user_data.get('reminder_date', '')}`\n\n"
            "⏰ **مرحله ۲ از ۳ - انتخاب ساعت**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "⏰ **مرحله ۲ از ۳ - انتخاب ساعت**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return TIME

async def time_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش انتخاب ساعت"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.replace("time_", "")
    
    if data == "manual":
        await query.edit_message_text(
            "⏰ **ساعت را به فرمت `HH:MM` وارد کنید**\n"
            "مثال: `14:30`"
        )
        return TIME
    
    context.user_data['reminder_time'] = data
    
    # رفتن به مرحله عنوان
    await query.edit_message_text(
        f"📅 تاریخ: `{context.user_data.get('reminder_date', '')}`\n"
        f"⏰ ساعت: `{data}`\n\n"
        "📝 **مرحله ۳ از ۳**\n"
        "لطفاً عنوان یادآوری را وارد کنید:"
    )
    return TITLE

async def get_manual_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت تاریخ دستی"""
    try:
        date_str = update.message.text.strip()
        datetime.strptime(date_str, "%Y-%m-%d")
        context.user_data['reminder_date'] = date_str
        await update.message.delete()
        
        # نمایش انتخاب ساعت
        keyboard = []
        row = []
        for label, time in QUICK_TIMES:
            row.append(InlineKeyboardButton(label, callback_data=f"time_{time}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("⏰ انتخاب دستی", callback_data="time_manual")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به تاریخ", callback_data="back_to_date")])
        
        await update.message.reply_text(
            f"📅 تاریخ انتخاب‌شده: `{date_str}`\n\n"
            "⏰ **مرحله ۲ از ۳ - انتخاب ساعت**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return TIME
    except:
        await update.message.reply_text(
            "❌ فرمت تاریخ اشتباه است!\n"
            "لطفاً به فرمت `YYYY-MM-DD` وارد کنید.\n"
            "مثال: `2025-12-25`"
        )
        return DATE

async def get_manual_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت ساعت دستی"""
    try:
        time_str = update.message.text.strip()
        datetime.strptime(time_str, "%H:%M")
        context.user_data['reminder_time'] = time_str
        await update.message.delete()
        
        await update.message.reply_text(
            f"📅 تاریخ: `{context.user_data.get('reminder_date', '')}`\n"
            f"⏰ ساعت: `{time_str}`\n\n"
            "📝 **مرحله ۳ از ۳**\n"
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
    """دریافت عنوان و ذخیره یادآوری"""
    title = update.message.text.strip()
    context.user_data['reminder_title'] = title
    await update.message.delete()
    
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
            f"🆔 شناسه: `{reminder_id}`"
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
    
    text += "برای لغو: /cancel_reminder [شناسه]"
    await update.message.reply_text(text)

async def cancel_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو یادآوری"""
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ لطفاً شناسه را وارد کنید.\n"
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
            await update.message.reply_text(f"✅ یادآوری با شناسه `{reminder_id}` لغو شد.")
        else:
            await update.message.reply_text(f"❌ یادآوری با شناسه `{reminder_id}` پیدا نشد.")
        db.close()
        
    except ValueError:
        await update.message.reply_text("❌ شناسه باید عدد باشد.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

async def back_to_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت به انتخاب تاریخ"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    row = []
    for label, days in QUICK_DATES:
        row.append(InlineKeyboardButton(label, callback_data=f"date_{days}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("📅 انتخاب دستی", callback_data="date_manual")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")])
    
    await query.edit_message_text(
        "📅 **انتخاب تاریخ**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return DATE
