from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    keyboard = [
        [InlineKeyboardButton("💬 گفتگو با دستیار", callback_data="chat_menu")],
        [InlineKeyboardButton("⏰ یادآوری‌ها", callback_data="reminder_menu")],
        [InlineKeyboardButton("📊 تاریخچه احساسات", callback_data="history_menu")],
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile_menu")]
    ]

    text = "📋 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید."

    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['current_section'] = 'chat'
    await query.edit_message_text(
        "💬 **بخش گفتگو با دستیار**\n\n"
        "هر سوالی دارید، بپرسید. من اینجام تا کمکت کنم.\n"
        "برای بازگشت به منو، دکمه زیر را بزنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ])
    )

async def reminder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⏰ **بخش یادآوری‌ها**\n\n"
        "برای تنظیم یادآوری، پیام خود را به این شکل ارسال کنید:\n"
        "`2025-01-15 14:30 | عنوان یادآوری`\n\n"
        "برای دیدن لیست یادآوری‌ها، /listreminders را بزنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ])
    )
    context.user_data['current_section'] = 'reminder'

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
