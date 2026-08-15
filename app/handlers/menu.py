from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اصلی با دکمه‌های شیشه‌ای"""
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    keyboard = [
        [InlineKeyboardButton("💬 چت با دستیار", callback_data="chat_menu")],
        [InlineKeyboardButton("⏰ یادآوری‌ها", callback_data="reminder_menu")],
        [InlineKeyboardButton("📊 تاریخچه من", callback_data="history_menu")],
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile_menu")]
    ]
    
    text = "🤖 **به منوی اصلی خوش اومدی!**\n\nاز دکمه‌های زیر یکی رو انتخاب کن:"
    
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به بخش چت"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💬 **بخش چت با دستیار**\n\n"
        "هر سوالی داری بپرس، من اینجام تا کمک کنم.\n"
        "برای بازگشت به منو، /menu رو بزن."
    )
    # ذخیره وضعیت کاربر در context
    context.user_data['current_section'] = 'chat'

async def reminder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به بخش یادآوری"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⏰ **بخش یادآوری‌ها**\n\n"
        "برای تنظیم یادآوری جدید، دستور /remind رو بزن.\n"
        "برای دیدن لیست یادآوری‌ها، /listreminders رو بزن.\n"
        "برای لغو یادآوری، /cancel_reminder [شناسه] رو بزن.\n\n"
        "برای بازگشت به منو، /menu رو بزن."
    )
    context.user_data['current_section'] = 'reminder'

async def history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به بخش تاریخچه"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📊 **بخش تاریخچه‌ی احساسات**\n\n"
        "برای ثبت احساس امروز: /mood [خوب/بد/معمولی]\n"
        "برای دیدن تاریخچه: /history\n\n"
        "برای بازگشت به منو، /menu رو بزن."
    )
    context.user_data['current_section'] = 'history'

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پروفایل کاربر"""
    query = update.callback_query
    await query.answer()
    # اینجا باید profile.show_profile رو صدا بزنی
    from app.handlers import profile
    await profile.show_profile(update, context)
