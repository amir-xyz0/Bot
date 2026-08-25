import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
        try:
            await message.delete()
        except:
            pass
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
                "❗ ثبت‌نام نکرده‌اید.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            db.close()
            return

        context.user_data['editing'] = None
        context.user_data['edit_question_id'] = None

        # استفاده از getattr برای جلوگیری از خطا در صورت نبودن فیلد
        morning_enabled = getattr(user, 'morning_msg_enabled', True)
        night_enabled = getattr(user, 'night_msg_enabled', True)
        notifications = getattr(user, 'notifications', True)

        text = (
            f"👤 **پروفایل شما**\n\n"
            f"نام: {user.preferred_name or 'تعیین نشده'}\n"
            f"جنسیت: {'مرد' if user.gender == 'male' else 'زن' if user.gender == 'female' else 'تعیین نشده'}\n"
            f"سن: {user.age or 'تعیین نشده'}\n"
            f"سبک گفتگو: {user.chat_style or 'تعیین نشده'}\n"
            f"🌅 اعلان صبح: {'✅ فعال' if morning_enabled else '❌ غیرفعال'}\n"
            f"🌙 اعلان شب: {'✅ فعال' if night_enabled else '❌ غیرفعال'}\n"
            f"🔔 اعلان‌ها: {'✅ فعال' if notifications else '❌ غیرفعال'}"
        )

        keyboard = [
            [InlineKeyboardButton("✏️ ویرایش نام", callback_data="edit_name")],
            [InlineKeyboardButton("✏️ ویرایش جنسیت", callback_data="edit_gender")],
            [InlineKeyboardButton("✏️ ویرایش سن", callback_data="edit_age")],
            [InlineKeyboardButton("✏️ ویرایش سبک گفتگو", callback_data="edit_style")],
            [InlineKeyboardButton("🌅 تنظیم اعلان صبح", callback_data="edit_morning")],
            [InlineKeyboardButton("🌙 تنظیم اعلان شب", callback_data="edit_night")],
            [InlineKeyboardButton("🔔 تنظیم اعلان‌ها", callback_data="edit_notifications")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
        ]
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"❌ خطا در نمایش پروفایل: {e}")
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(
            "❌ خطایی در نمایش پروفایل رخ داد.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        db.close()

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    try:
        await query.message.delete()
    except:
        pass
    
    context.user_data['editing'] = 'name'
    keyboard = [[InlineKeyboardButton("🔙 لغو", callback_data="profile_menu")]]
    msg = await query.message.reply_text(
        "✏️ نام جدید خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['edit_question_id'] = msg.message_id

async def process_name_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    new_name = update.message.text.strip()
    
    try:
        await update.message.delete()
    except:
        pass
    
    question_id = context.user_data.get('edit_question_id')
    if question_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=question_id)
            context.user_data['edit_question_id'] = None
        except:
            pass
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.preferred_name = new_name
            db.commit()
            context.user_data['editing'] = None
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="profile_menu")]]
            await update.message.reply_text(
                f"✅ نام شما با موفقیت به **{new_name}** تغییر یافت.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            logger.info(f"✅ نام کاربر {user_id} به {new_name} تغییر کرد")
        else:
            await update.message.reply_text("❗ کاربر یافت نشد.")
    except Exception as e:
        logger.error(f"❌ خطا در ویرایش نام: {e}")
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کن.")
    finally:
        db.close()

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
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="profile_menu")]]
            await query.edit_message_text(
                "✅ جنسیت با موفقیت به‌روزرسانی شد.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
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
    user_id = update.effective_user.id
    
    try:
        await query.message.delete()
    except:
        pass
    
    context.user_data['editing'] = 'age'
    keyboard = [[InlineKeyboardButton("🔙 لغو", callback_data="profile_menu")]]
    msg = await query.message.reply_text(
        "✏️ سن خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['edit_question_id'] = msg.message_id

async def process_age_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    age_text = update.message.text.strip()
    
    try:
        await update.message.delete()
    except:
        pass
    
    question_id = context.user_data.get('edit_question_id')
    if question_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=question_id)
            context.user_data['edit_question_id'] = None
        except:
            pass
    
    if not age_text.isdigit():
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کن.")
        return
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.age = int(age_text)
            db.commit()
            context.user_data['editing'] = None
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="profile_menu")]]
            await update.message.reply_text(
                f"✅ سن شما با موفقیت به **{age_text}** تغییر یافت.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            logger.info(f"✅ سن کاربر {user_id} به {age_text} تغییر کرد")
        else:
            await update.message.reply_text("❗ کاربر یافت نشد.")
    except Exception as e:
        logger.error(f"❌ خطا در ویرایش سن: {e}")
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کن.")
    finally:
        db.close()

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
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="profile_menu")]]
            await query.edit_message_text(
                "✅ سبک گفتگو با موفقیت به‌روزرسانی شد.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
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
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="profile_menu")]]
            await query.edit_message_text(
                f"✅ اعلان‌ها {status} شدند.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("❗ کاربر یافت نشد.")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
        await query.edit_message_text("❌ خطایی رخ داد.")
    finally:
        db.close()

async def edit_morning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.morning_msg_enabled = not user.morning_msg_enabled
            db.commit()
            status = "فعال" if user.morning_msg_enabled else "غیرفعال"
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="profile_menu")]]
            await query.edit_message_text(
                f"✅ اعلان صبح {status} شد.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("❗ کاربر یافت نشد.")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
        await query.edit_message_text("❌ خطایی رخ داد.")
    finally:
        db.close()

async def edit_night(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            # استفاده از getattr برای جلوگیری از خطا
            if hasattr(user, 'night_msg_enabled'):
                user.night_msg_enabled = not user.night_msg_enabled
            else:
                # اگر فیلد وجود نداشت، یک مقدار پیش‌فرض بذار
                user.night_msg_enabled = False
            db.commit()
            status = "فعال" if user.night_msg_enabled else "غیرفعال"
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="profile_menu")]]
            await query.edit_message_text(
                f"✅ اعلان شب {status} شد.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("❗ کاربر یافت نشد.")
    except Exception as e:
        logger.error(f"❌ خطا در ویرایش اعلان شب: {e}")
        await query.edit_message_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کن.")
    finally:
        db.close()

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['editing'] = None
    context.user_data['edit_question_id'] = None
    
    try:
        await query.message.delete()
    except:
        pass
    
    await show_profile(update, context)
