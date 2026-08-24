import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

# States
NAME, GENDER, AGE, STYLE = range(4)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # حذف پیام قبلی (دکمه شروع ثبت‌نام)
    try:
        await query.message.delete()
    except:
        pass
    
    msg = await query.message.reply_text(
        "📝 **ثبت‌نام**\n\n"
        "به ربات همراه و مشاوره شخصی خوش آمدی!\n"
        "برای شروع، لطفاً نام خود را وارد کن:"
    )
    # ذخیره message_id پیام ربات برای حذف بعدی
    context.user_data['last_bot_message_id'] = msg.message_id
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.message.text
    
    # حذف پیام کاربر
    try:
        await update.message.delete()
    except:
        pass
    
    # حذف پیام ربات قبلی (سوال نام)
    try:
        last_msg_id = context.user_data.get('last_bot_message_id')
        if last_msg_id:
            await context.bot.delete_message(chat_id=user_id, message_id=last_msg_id)
    except:
        pass
    
    context.user_data['preferred_name'] = name
    
    keyboard = [
        [InlineKeyboardButton("👨 مرد", callback_data="gender_male")],
        [InlineKeyboardButton("👩 زن", callback_data="gender_female")]
    ]
    msg = await update.message.reply_text(
        f"👋 خوش آمدی **{name}**!\n\n"
        "جنسیت خود را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['last_bot_message_id'] = msg.message_id
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    gender = query.data.split("_")[1]
    
    # حذف پیام ربات قبلی (سوال جنسیت)
    try:
        last_msg_id = context.user_data.get('last_bot_message_id')
        if last_msg_id:
            await context.bot.delete_message(chat_id=user_id, message_id=last_msg_id)
    except:
        pass
    
    context.user_data['gender'] = gender
    
    msg = await query.message.reply_text(
        "📅 **سن خود را وارد کن:**\n\n"
        "(فقط عدد وارد کن، مثلاً ۲۵)"
    )
    context.user_data['last_bot_message_id'] = msg.message_id
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    age_text = update.message.text
    
    # حذف پیام کاربر
    try:
        await update.message.delete()
    except:
        pass
    
    # حذف پیام ربات قبلی (سوال سن)
    try:
        last_msg_id = context.user_data.get('last_bot_message_id')
        if last_msg_id:
            await context.bot.delete_message(chat_id=user_id, message_id=last_msg_id)
    except:
        pass
    
    if not age_text.isdigit():
        msg = await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن.")
        context.user_data['last_bot_message_id'] = msg.message_id
        return AGE
    
    context.user_data['age'] = int(age_text)
    
    keyboard = [
        [InlineKeyboardButton("🤗 دوستانه", callback_data="style_friendly")],
        [InlineKeyboardButton("🧐 رسمی", callback_data="style_formal")],
        [InlineKeyboardButton("😂 طنز", callback_data="style_funny")],
        [InlineKeyboardButton("🧘 آرام", callback_data="style_calm")]
    ]
    msg = await update.message.reply_text(
        "🎭 **سبک گفتگو را انتخاب کن:**\n\n"
        "این سبک در بخش «گفتگوی همراه» استفاده میشه.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['last_bot_message_id'] = msg.message_id
    return STYLE

async def get_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    style = query.data.split("_")[1]
    
    # حذف پیام ربات قبلی (سوال سبک)
    try:
        last_msg_id = context.user_data.get('last_bot_message_id')
        if last_msg_id:
            await context.bot.delete_message(chat_id=user_id, message_id=last_msg_id)
    except:
        pass
    
    # ذخیره در دیتابیس
    db = SessionLocal()
    try:
        user = User(
            user_id=user_id,
            preferred_name=context.user_data['preferred_name'],
            gender=context.user_data['gender'],
            age=context.user_data['age'],
            chat_style=style,
            notifications=True,
            morning_msg_enabled=True,
            mood_history=[]
        )
        db.add(user)
        db.commit()
        logger.info(f"✅ کاربر {user_id} ثبت‌نام کرد.")
        
        # حذف پیام انتخاب سبک
        try:
            await query.message.delete()
        except:
            pass
        
        keyboard = [[InlineKeyboardButton("🏠 رفتن به خانه", callback_data="main_menu")]]
        await query.message.reply_text(
            "✅ **ثبت‌نام شما با موفقیت کامل شد!**\n\n"
            "به جمع کاربران ربات همراه خوش آمدی. 🌸\n"
            "حالا می‌تونی از همه بخش‌ها استفاده کنی.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره کاربر: {e}")
        await query.message.reply_text("❌ خطایی در ثبت‌نام رخ داد. لطفاً دوباره /start را بزنید.")
    finally:
        db.close()
    
    # پاک کردن dataهای موقت
    context.user_data.clear()
    return -1
