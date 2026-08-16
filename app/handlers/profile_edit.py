from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()

    if not user:
        await update.message.reply_text("❌ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        return

    gender_map = {"male": "مرد", "female": "زن"}
    style_map = {"friendly": "دوستانه", "formal": "رسمی", "funny": "طنز", "calm": "آرام"}

    text = (
        f"👤 **پروفایل شما**\n\n"
        f"نام: {user.preferred_name}\n"
        f"جنسیت: {gender_map.get(user.gender, 'نامشخص')}\n"
        f"سن: {user.age}\n"
        f"لحن: {style_map.get(user.chat_style, 'نامشخص')}\n"
        f"وضعیت: {'💎 پریمیوم' if user.is_premium else '🆓 رایگان'}\n"
        f"اعلان صبح: {'✅ فعال' if user.morning_msg_enabled else '❌ غیرفعال'}\n"
        f"اعلان شب: {'✅ فعال' if user.night_msg_enabled else '❌ غیرفعال'}"
    )

    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش نام", callback_data="edit_name")],
        [InlineKeyboardButton("🔄 تغییر جنسیت", callback_data="edit_gender")],
        [InlineKeyboardButton("🔄 تغییر سن", callback_data="edit_age")],
        [InlineKeyboardButton("🔄 تغییر لحن", callback_data="edit_style")],
        [InlineKeyboardButton("🔔 تغییر تنظیمات اعلان", callback_data="edit_notifications")],
        [InlineKeyboardButton("📋 بازگشت به منو", callback_data="main_menu")]
    ]
    
    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['edit_type'] = 'name'
    await query.edit_message_text("📝 نام جدید خود را وارد کنید:")

async def edit_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("👨 مرد", callback_data="set_gender_male")],
        [InlineKeyboardButton("👩 زن", callback_data="set_gender_female")]
    ]
    await query.edit_message_text("👤 جنسیت جدید خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = "male" if "male" in query.data else "female"
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    if user:
        user.gender = gender
        db.commit()
    db.close()
    await query.edit_message_text("✅ جنسیت با موفقیت تغییر کرد!")
    await show_profile(update, context)

async def edit_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['edit_type'] = 'age'
    await query.edit_message_text("📅 سن جدید خود را وارد کنید (عدد):")

async def edit_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🤗 دوستانه", callback_data="set_style_friendly")],
        [InlineKeyboardButton("👔 رسمی", callback_data="set_style_formal")],
        [InlineKeyboardButton("😂 طنز", callback_data="set_style_funny")],
        [InlineKeyboardButton("🧘 آرام", callback_data="set_style_calm")]
    ]
    await query.edit_message_text("🎭 لحن جدید خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    style = query.data.replace("set_style_", "")
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    if user:
        user.chat_style = style
        db.commit()
    db.close()
    await query.edit_message_text("✅ لحن با موفقیت تغییر کرد!")
    await show_profile(update, context)

async def edit_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    if user:
        user.morning_msg_enabled = not user.morning_msg_enabled
        user.night_msg_enabled = not user.night_msg_enabled
        db.commit()
    db.close()
    await query.edit_message_text("✅ تنظیمات اعلان با موفقیت تغییر کرد!")
    await show_profile(update, context)

async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    edit_type = context.user_data.get('edit_type')
    if not edit_type:
        return
    
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    
    if edit_type == 'name':
        user.preferred_name = update.message.text
        db.commit()
        await update.message.reply_text("✅ نام با موفقیت تغییر کرد!")
    elif edit_type == 'age':
        try:
            age = int(update.message.text)
            if 10 <= age <= 100:
                user.age = age
                db.commit()
                await update.message.reply_text("✅ سن با موفقیت تغییر کرد!")
            else:
                await update.message.reply_text("❌ لطفاً عددی بین ۱۰ تا ۱۰۰ وارد کنید.")
        except:
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید.")
    
    db.close()
    context.user_data['edit_type'] = None
    await show_profile(update, context)
