from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.database import SessionLocal
from app.models import User

# تعریف وضعیت‌های ConversationHandler
NAME, GENDER, AGE, STYLE = range(4)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرآیند ثبت‌نام - دریافت اسم"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👋 سلام! اسمت چیه؟ دوست دارم چطور صدات کنم؟"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت اسم کاربر و رفتن به مرحله‌ی جنسیت"""
    context.user_data["preferred_name"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("👨 مرد", callback_data="male")],
        [InlineKeyboardButton("👩 زن", callback_data="female")]
    ]
    await update.message.reply_text(
        "جنسیتت رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت جنسیت و رفتن به مرحله‌ی سن"""
    query = update.callback_query
    await query.answer()
    context.user_data["gender"] = query.data  # "male" یا "female"
    
    await query.edit_message_text(
        "📅 چند سالته؟ (عدد وارد کن)"
    )
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت سن و رفتن به مرحله‌ی انتخاب لحن"""
    try:
        age = int(update.message.text)
        if age < 10 or age > 100:
            raise ValueError
        context.user_data["age"] = age
        
        keyboard = [
            [InlineKeyboardButton("🤗 دوستانه", callback_data="friendly")],
            [InlineKeyboardButton("👔 رسمی", callback_data="formal")],
            [InlineKeyboardButton("😂 طنز", callback_data="funny")],
            [InlineKeyboardButton("🧘 آرام", callback_data="calm")]
        ]
        await update.message.reply_text(
            "لحن مورد علاقت رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return STYLE
    except:
        await update.message.reply_text(
            "❌ لطفاً یک عدد معتبر بین ۱۰ تا ۱۰۰ وارد کن."
        )
        return AGE

async def get_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت لحن، ذخیره در دیتابیس و پایان ثبت‌نام"""
    query = update.callback_query
    await query.answer()
    context.user_data["chat_style"] = query.data
    
    # ذخیره در دیتابیس
    db = SessionLocal()
    user = User(
        user_id=update.effective_user.id,
        preferred_name=context.user_data["preferred_name"],
        gender=context.user_data["gender"],
        age=context.user_data["age"],
        chat_style=context.user_data["chat_style"]
    )
    db.add(user)
    db.commit()
    db.close()
    
    # هدایت به منوی اصلی
    from app.handlers.menu import main_menu
    await query.edit_message_text(
        f"✅ ثبت‌نام کامل شد!\n\n"
        f"خوش اومدی {context.user_data['preferred_name']}!\n"
        f"از این به بعد من دستیار تو هستم."
    )
    # ساخت یک Update جدید برای هدایت به منو
    await main_menu(update, context)
    return ConversationHandler.END

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش اطلاعات پروفایل کاربر"""
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        await update.message.reply_text(
            "❌ شما ثبت‌نام نکردید!\n"
            "لطفاً /start رو بزنید و ثبت‌نام کنید."
        )
        return
    
    # ترجمه جنسیت به فارسی
    gender_map = {
        "male": "مرد",
        "female": "زن"
    }
    gender_fa = gender_map.get(user.gender, "نامشخص")
    
    # ترجمه لحن به فارسی
    style_map = {
        "friendly": "دوستانه 🤗",
        "formal": "رسمی 👔",
        "funny": "طنز 😂",
        "calm": "آرام 🧘"
    }
    style_fa = style_map.get(user.chat_style, "نامشخص")
    
    text = (
        f"👤 **پروفایل تو**\n\n"
        f"نام: {user.preferred_name}\n"
        f"جنسیت: {gender_fa}\n"
        f"سن: {user.age}\n"
        f"لحن: {style_fa}\n"
        f"وضعیت: {'💎 پریمیوم' if user.is_premium else '🆓 رایگان'}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش پروفایل", callback_data="edit_profile")],
        [InlineKeyboardButton("🔔 تنظیمات پیام‌ها", callback_data="msg_settings")],
        [InlineKeyboardButton("📋 بازگشت به منو", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
