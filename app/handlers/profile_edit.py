import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        logger.info(f"👤 نمایش پروفایل: user_id={user_id}")

        db = SessionLocal()
        user = db.query(User).filter_by(user_id=user_id).first()
        db.close()

        if not user:
            await update.message.reply_text("❗ ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
            return

        gender_map = {"male": "مرد", "female": "زن"}
        style_map = {"friendly": "دوستانه 🤗", "formal": "رسمی 👔", "funny": "طنز 😂", "calm": "آرام 🧘"}

        text = (
            f"👤 **پروفایل من**\n\n"
            f"🌸 نام: {user.preferred_name}\n"
            f"⚧️ جنسیت: {gender_map.get(user.gender, 'نامشخص')}\n"
            f"🎂 سن: {user.age}\n"
            f"🎭 لحن: {style_map.get(user.chat_style, 'نامشخص')}\n"
            f"🌅 اعلان صبح: {'✅ فعال' if user.morning_msg_enabled else '❌ غیرفعال'}\n"
            f"🌙 اعلان شب: {'✅ فعال' if user.night_msg_enabled else '❌ غیرفعال'}"
        )

        keyboard = [
            [InlineKeyboardButton("✏️ ویرایش نام", callback_data="edit_name"),
             InlineKeyboardButton("🔄 تغییر جنسیت", callback_data="edit_gender")],
            [InlineKeyboardButton("🔄 تغییر سن", callback_data="edit_age"),
             InlineKeyboardButton("🔄 تغییر لحن", callback_data="edit_style")],
            [InlineKeyboardButton("🔔 تنظیم اعلان‌ها", callback_data="edit_notifications")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
        ]

        if update.callback_query:
            query = update.callback_query
            await query.answer()
            try:
                await query.message.delete()
            except:
                pass
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"❌ خطا در نمایش پروفایل: {e}")
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# ============================================================
# توابع ویرایش (همگی با ظاهر زیبا و حذف پیام‌ها)
# ============================================================

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['edit_type'] = 'name'
    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text(
        "✏️ **ویرایش نام**\n\n"
        "نام جدید خود را وارد کن تا با آن صدایت کنم..."
    )

async def edit_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("👨 مرد", callback_data="set_gender_male"),
         InlineKeyboardButton("👩 زن", callback_data="set_gender_female")]
    ]
    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text(
        "⚧️ **تغییر جنسیت**\n\n"
        "جنسیت جدید خود را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = "male" if "male" in query.data else "female"
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.gender = gender
            db.commit()
            logger.info(f"✅ جنسیت کاربر {user_id} به {gender} تغییر کرد")
    except Exception as e:
        logger.error(f"❌ خطا در تغییر جنسیت: {e}")
    finally:
        db.close()

    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text("✅ جنسیت با موفقیت تغییر کرد!")
    await show_profile(update, context)

async def edit_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['edit_type'] = 'age'
    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text(
        "🎂 **ویرایش سن**\n\n"
        "سن جدید خود را وارد کن (عدد)..."
    )

async def edit_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🤗 دوستانه", callback_data="set_style_friendly"),
         InlineKeyboardButton("👔 رسمی", callback_data="set_style_formal")],
        [InlineKeyboardButton("😂 طنز", callback_data="set_style_funny"),
         InlineKeyboardButton("🧘 آرام", callback_data="set_style_calm")]
    ]
    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text(
        "🎭 **تغییر لحن**\n\n"
        "لحن جدید مورد علاقه‌ات را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    style = query.data.replace("set_style_", "")
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.chat_style = style
            db.commit()
            logger.info(f"✅ لحن کاربر {user_id} به {style} تغییر کرد")
    except Exception as e:
        logger.error(f"❌ خطا در تغییر لحن: {e}")
    finally:
        db.close()

    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text("✅ لحن با موفقیت تغییر کرد!")
    await show_profile(update, context)

async def edit_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.morning_msg_enabled = not user.morning_msg_enabled
            user.night_msg_enabled = not user.night_msg_enabled
            db.commit()
            logger.info(f"✅ تنظیمات اعلان کاربر {user_id} تغییر کرد")
    except Exception as e:
        logger.error(f"❌ خطا در تغییر تنظیمات اعلان: {e}")
    finally:
        db.close()

    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text(
        "🔔 **تنظیمات اعلان**\n\n"
        f"✅ اعلان صبح: {'فعال' if user.morning_msg_enabled else 'غیرفعال'}\n"
        f"✅ اعلان شب: {'فعال' if user.night_msg_enabled else 'غیرفعال'}"
    )
    await show_profile(update, context)

async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    edit_type = context.user_data.get('edit_type')
    if not edit_type:
        return

    user_id = update.effective_user.id
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ کاربر پیدا نشد.")
            return

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
                    await update.message.reply_text("❌ لطفاً عددی بین ۱۰ تا ۱۰۰ وارد کن.")
            except:
                await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن.")
    except Exception as e:
        logger.error(f"❌ خطا در handle_edit_input: {e}")
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کن.")
    finally:
        db.close()

    context.user_data['edit_type'] = None
    await show_profile(update, context)
