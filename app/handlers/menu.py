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
        [InlineKeyboardButton("گفتگو با دستیار", callback_data="chat_menu")],
        [InlineKeyboardButton("یادآوری‌ها", callback_data="reminder_menu")],
        [InlineKeyboardButton("تاریخچه احساسات", callback_data="history_menu")],
        [InlineKeyboardButton("پروفایل", callback_data="profile_menu")]
    ]
    
    text = "منوی اصلی:\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید."
    
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "بخش گفتگو با دستیار:\n"
        "هر سوالی دارید، بپرسید.\n"
        "برای بازگشت به منو، دکمه زیر را بزنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بازگشت به منو", callback_data="main_menu")]
        ])
    )
    context.user_data['current_section'] = 'chat'

async def reminder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "بخش یادآوری‌ها:\n"
        "برای تنظیم یادآوری، دکمه زیر را بزنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("تنظیم یادآوری جدید", callback_data="set_reminder")],
            [InlineKeyboardButton("بازگشت به منو", callback_data="main_menu")]
        ])
    )
    context.user_data['current_section'] = 'reminder'

async def history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "بخش تاریخچه احساسات:\n"
        "برای ثبت احساس امروز یا مشاهده تاریخچه، از دکمه‌های زیر استفاده کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ثبت احساس امروز", callback_data="record_mood")],
            [InlineKeyboardButton("مشاهده تاریخچه", callback_data="show_history")],
            [InlineKeyboardButton("بازگشت به منو", callback_data="main_menu")]
        ])
    )
    context.user_data['current_section'] = 'history'

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from app.handlers import profile
    await profile.show_profile(update, context)
