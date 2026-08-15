from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.database import SessionLocal
from app.models import User

NAME, GENDER, AGE, STYLE = range(4)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("لطفاً نام خود را وارد کنید:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["preferred_name"] = update.message.text
    await update.message.delete()
    
    keyboard = [
        [InlineKeyboardButton("مرد", callback_data="male")],
        [InlineKeyboardButton("زن", callback_data="female")]
    ]
    await update.message.reply_text(
        "جنسیت خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["gender"] = query.data
    await query.edit_message_text("سن خود را وارد کنید (عدد):")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        if age < 10 or age > 100:
            raise ValueError
        context.user_data["age"] = age
        await update.message.delete()
        
        keyboard = [
            [InlineKeyboardButton("دوستانه", callback_data="friendly")],
            [InlineKeyboardButton("رسمی", callback_data="formal")],
            [InlineKeyboardButton("طنز", callback_data="funny")],
            [InlineKeyboardButton("آرام", callback_data="calm")]
        ]
        await update.message.reply_text(
            "لحن مورد نظر خود را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return STYLE
    except:
        await update.message.reply_text("لطفاً یک عدد معتبر بین ۱۰ تا ۱۰۰ وارد کنید.")
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
    
    from app.handlers.menu import main_menu
    await query.edit_message_text("ثبت‌نام با موفقیت انجام شد.")
    await main_menu(update, context)
    return ConversationHandler.END

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        await update.message.reply_text("شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        return
    
    gender_map = {"male": "مرد", "female": "زن"}
    style_map = {"friendly": "دوستانه", "formal": "رسمی", "funny": "طنز", "calm": "آرام"}
    
    text = (
        f"پروفایل شما:\n"
        f"نام: {user.preferred_name}\n"
        f"جنسیت: {gender_map.get(user.gender, 'نامشخص')}\n"
        f"سن: {user.age}\n"
        f"لحن: {style_map.get(user.chat_style, 'نامشخص')}\n"
        f"وضعیت: {'پریمیوم' if user.is_premium else 'رایگان'}"
    )
    
    keyboard = [[InlineKeyboardButton("بازگشت به منو", callback_data="main_menu")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
