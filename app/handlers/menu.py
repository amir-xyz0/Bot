from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اصلی - هم برای callback و هم برای پیام معمولی"""
    # تشخیص نوع درخواست
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        # سعی می‌کنیم پیام قبلی رو ویرایش کنیم، اگر نشد پیام جدید می‌فرستیم
        try:
            await query.message.delete()  # حذف پیام قبلی
            message = await query.message.reply_text("⏳ در حال بارگذاری...")
        except:
            message = await query.message.reply_text("⏳ در حال بارگذاری...")
    else:
        message = update.message

    keyboard = [
        [InlineKeyboardButton("💬 گفتگو با دستیار", callback_data="chat_menu")],
        [InlineKeyboardButton("📊 تاریخچه احساسات", callback_data="history_menu")],
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile_menu")]
    ]

    text = "📋 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    
    # اگر پیام قبلاً وجود داشته و قابل ویرایشه، ویرایشش کن، وگرنه جدید بفرست
    try:
        if update.callback_query:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        # اگر ویرایش نشد (مثلاً پیام قبلی حذف شده)، پیام جدید بفرست
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['current_section'] = 'chat'
    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text(
        "💬 **بخش گفتگو با دستیار**\n\n"
        "هر سوالی دارید، بپرسید. من اینجام تا کمکت کنم.\n"
        "برای بازگشت به منو، دکمه زیر را بزنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ])
    )

async def history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from app.handlers import history
    await history.show_history(update, context)

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from app.handlers import profile_edit
    await profile_edit.show_profile(update, context)
