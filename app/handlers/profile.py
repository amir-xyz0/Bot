from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.database import SessionLocal
from app.models import User

NAME, GENDER, AGE, STYLE = range(4)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # حذف پیام قبلی (صفحه خوش‌آمدگویی)
    try:
        await query.message.delete()
    except Exception:
        pass
    
    # ارسال پیام جدید
    msg = await query.message.reply_text("📝 **لطفاً نام خود را وارد کنید:**")
    context.user_data['msg_id'] = msg.message_id
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ذخیره اسم کاربر
    context.user_data["preferred_name"] = update.message.text
    
    # حذف پیام کاربر (با try/except کامل)
    try:
        await update.message.delete()
    except Exception as e:
        print(f"خطا در حذف پیام کاربر: {e}")
    
    # حذف پیام قبلی ربات (با try/except کامل)
    try:
        if 'msg_id' in context.user_data:
            await update.message.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['msg_id']
            )
    except Exception as e:
        print(f"خطا در حذف پیام ربات: {e}")
    
    # نمایش دکمه‌های جنسیت
    keyboard = [
        [InlineKeyboardButton("👨 مرد", callback_data="male")],
        [InlineKeyboardButton("👩 زن", callback_data="female")]
    ]
    msg = await update.message.reply_text(
        "👤 **جنسیت خود را انتخاب کنید:**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['msg_id'] = msg.message_id
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["gender"] = query.data
    
    # حذف پیام قبلی
    try:
        await query.message.delete()
    except Exception:
        pass
    
    msg = await query.message.reply_text("📅 **سن خود را وارد کنید (عدد):**")
    context.user_data['msg_id'] = msg.message_id
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        if age < 10 or age > 100:
            raise ValueError
        
        context.user_data["age"] = age
        
        # حذف پیام کاربر
        try:
            await update.message.delete()
        except Exception:
            pass
        
        # حذف پیام قبلی ربات
        try:
            if 'msg_id' in context.user_data:
                await update.message.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data['msg_id']
                )
        except Exception:
            pass
        
        # نمایش دکمه‌های لحن
        keyboard = [
            [InlineKeyboardButton("🤗 دوستانه", callback_data="friendly")],
            [InlineKeyboardButton("👔 رسمی", callback_data="formal")],
            [InlineKeyboardButton("😂 طنز", callback_data="funny")],
            [InlineKeyboardButton("🧘 آرام", callback_data="calm")]
        ]
        msg = await update.message.reply_text(
            "🎭 **لحن مورد نظر خود را انتخاب کنید:**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data['msg_id'] = msg.message_id
        return STYLE
        
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر بین ۱۰ تا ۱۰۰ وارد کنید.")
        return AGE

async def get_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["chat_style"] = query.data
    
    # حذف پیام قبلی
    try:
        await query.message.delete()
    except Exception:
        pass
    
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
    
    # پیام تبریک
    await query.message.reply_text("✅ **ثبت‌نام با موفقیت انجام شد!**")
    
    # هدایت به منوی اصلی
    from app.handlers.menu import main_menu
    await main_menu(update, context)
    return ConversationHandler.END
