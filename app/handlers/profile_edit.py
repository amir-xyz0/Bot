import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # تشخیص اینکه از callback_query اومده یا نه
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    if not message:
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            await message.reply_text(
                "❗ ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            db.close()
            return

        text = (
            f"👤 **پروفایل شما**\n\n"
            f"نام: {user.preferred_name or 'تعیین نشده'}\n"
            f"جنسیت: {'مرد' if user.gender == 'male' else 'زن' if user.gender == 'female' else 'تعیین نشده'}\n"
            f"سن: {user.age or 'تعیین نشده'}\n"
            f"سبک گفتگو: {user.chat_style or 'تعیین نشده'}\n"
            f"🌅 اعلان صبح: {'✅ فعال' if user.morning_msg_enabled else '❌ غیرفعال'}\n"
            f"🔔 اعلان‌ها: {'✅ فعال' if user.notifications else '❌ غیرفعال'}"
        )

        keyboard = [
            [InlineKeyboardButton("✏️ ویرایش نام", callback_data="edit_name")],
            [InlineKeyboardButton("✏️ ویرایش جنسیت", callback_data="edit_gender")],
            [InlineKeyboardButton("✏️ ویرایش سن", callback_data="edit_age")],
            [InlineKeyboardButton("✏️ ویرایش سبک گفتگو", callback_data="edit_style")],
            [InlineKeyboardButton("🔔 تنظیم اعلان‌ها", callback_data="edit_notifications")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"❌ خطا در نمایش پروفایل: {e}")
        await message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
    finally:
        db.close()

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['editing'] = 'name'
    keyboard = [[InlineKeyboardButton("🔙 لغو", callback_data="profile_menu")]]
    await query.edit_message_text(
        "✏️ نام جدید خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def edit_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("👨 مرد", callback_data="set_gender_male")],
        [InlineKeyboardButton("👩 زن", callback_data="set_gender_female")],
        [InlineKeyboardButton("🔙 لغو", callback_data="profile_menu")]
    ]
    await query.edit_message_text(
        "✏️ جنسیت خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    gender = query.data.split("_")[2]
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.gender = gender
            db.commit()
            await query.edit_message_text("✅ جنسیت با موفقیت به‌روزرسانی شد.")
        else:
            await query.edit_message_text("❗ کاربر یافت نشد.")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
        await query.edit_message_text("❌ خطایی رخ داد.")
    finally:
        db.close()

async def edit_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['editing'] = 'age'
    keyboard = [[InlineKeyboardButton("🔙 لغو", callback_data="profile_menu")]]
    await query.edit_message_text(
        "✏️ سن خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def edit_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🤗 دوستانه", callback_data="set_style_friendly")],
        [InlineKeyboardButton("🧐 رسمی", callback_data="set_style_formal")],
        [InlineKeyboardButton("😂 طنز", callback_data="set_style_funny")],
        [InlineKeyboardButton("🧘 آرام", callback_data="set_style_calm")],
        [InlineKeyboardButton("🔙 لغو", callback_data="profile_menu")]
    ]
    await query.edit_message_text(
        "✏️ سبک گفتگو را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    style = query.data.split("_")[2]
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.chat_style = style
            db.commit()
            await query.edit_message_text("✅ سبک گفتگو با موفقیت به‌روزرسانی شد.")
        else:
            await query.edit_message_text("❗ کاربر یافت نشد.")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
        await query.edit_message_text("❌ خطایی رخ داد.")
    finally:
        db.close()

async def edit_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.notifications = not user.notifications
            db.commit()
            status = "فعال" if user.notifications else "غیرفعال"
            await query.edit_message_text(f"✅ اعلان‌ها {status} شدند.")
        else:
            await query.edit_message_text("❗ کاربر یافت نشد.")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
        await query.edit_message_text("❌ خطایی رخ داد.")
    finally:
        db.close()
