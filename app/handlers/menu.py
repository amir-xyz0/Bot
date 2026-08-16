from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اصلی - همیشه پیام جدید ارسال می‌شود"""
    query = update.callback_query
    if query:
        await query.answer()
        # حذف پیام قبلی
        try:
            await query.message.delete()
        except:
            pass
        # ارسال پیام جدید
        await query.message.reply_text(
            "📋 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 گفتگو با دستیار", callback_data="chat_menu")],
                [InlineKeyboardButton("📊 تاریخچه احساسات", callback_data="history_menu")],
                [InlineKeyboardButton("👤 پروفایل", callback_data="profile_menu")]
            ])
        )
    else:
        # اگر از دستور /menu استفاده شده باشد
        await update.message.reply_text(
            "📋 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 گفتگو با دستیار", callback_data="chat_menu")],
                [InlineKeyboardButton("📊 تاریخچه احساسات", callback_data="history_menu")],
                [InlineKeyboardButton("👤 پروفایل", callback_data="profile_menu")]
            ])
        )

async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['current_section'] = 'chat'
    print(f"📌 current_section تنظیم شد به: {context.user_data['current_section']}")
    
    # حذف پیام قبلی
    try:
        await query.message.delete()
    except:
        pass
    
    # ارسال پیام جدید
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
    
    # حذف پیام قبلی
    try:
        await query.message.delete()
    except:
        pass
    
    from app.handlers import history
    await history.show_history(update, context)

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # حذف پیام قبلی
    try:
        await query.message.delete()
    except:
        pass
    
    from app.handlers import profile_edit
    await profile_edit.show_profile(update, context)
