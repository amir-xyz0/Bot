from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
        # حذف پیام‌های قبلی
        try:
            await query.message.delete()
        except:
            pass
    else:
        message = update.message

    keyboard = [
        [InlineKeyboardButton("💬 گفتگو با دستیار", callback_data="chat_menu")],
        [InlineKeyboardButton("⏰ یادآوری‌ها", callback_data="reminder_menu")],
        [InlineKeyboardButton("📊 تاریخچه احساسات", callback_data="history_menu")],
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile_menu")]
    ]

    text = "📋 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید."
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

async def reminder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text(
        "⏰ **بخش یادآوری‌ها**\n\n"
        "برای تنظیم یادآوری، لطفاً مراحل زیر را دنبال کنید:\n"
        "1️⃣ `/remind` را بزنید.\n"
        "2️⃣ تاریخ را به فرمت `YYYY-MM-DD` وارد کنید.\n"
        "3️⃣ ساعت را به فرمت `HH:MM` وارد کنید.\n"
        "4️⃣ عنوان یادآوری را وارد کنید.\n\n"
        "برای دیدن لیست یادآوری‌ها: /listreminders\n"
        "برای لغو: /cancel_reminder [شناسه]",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ])
    )

async def history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    from app.handlers import history
    await history.show_history(update, context)

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from app.handlers import profile_edit
    await profile_edit.show_profile(update, context)
