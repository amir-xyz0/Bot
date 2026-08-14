from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.database import SessionLocal
from app.models import User

NAME, GENDER, AGE, STYLE = range(4)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("اسمت چیه؟ دوست دارم چطور صدات کنم؟")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["preferred_name"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("👨 مرد", callback_data="male")],
        [InlineKeyboardButton("👩 زن", callback_data="female")],
        [InlineKeyboardButton("🌈 غیره", callback_data="other")]
    ]
    await update.message.reply_text("جنسیتت رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["gender"] = query.data
    await query.edit_message_text("چند سالته؟")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        if age < 10 or age > 100:
            raise ValueError
        context.user_data["age"] = age
        keyboard = [
            [InlineKeyboardButton("دوستانه 🤗", callback_data="friendly")],
            [InlineKeyboardButton("رسمی 👔", callback_data="formal")],
            [InlineKeyboardButton("طنز 😂", callback_data="funny")]
        ]
        await update.message.reply_text("لحن مورد علاقت رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
        return STYLE
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر بین ۱۰ تا ۱۰۰ وارد کن.")
        return AGE

async def get_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["chat_style"] = query.data
    
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
    
    await query.edit_message_text(
        f"🎉 ثبت‌نام کامل شد!\n\nخوش اومدی {context.user_data['preferred_name']}!\nاز این به بعد من دستیار تو هستم."
    )
    return ConversationHandler.END
