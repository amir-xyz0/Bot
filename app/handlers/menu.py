import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.handlers import past_self, therapist  # 🔥 ایمپورت درست

logger = logging.getLogger(__name__)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    keyboard = [
        [InlineKeyboardButton("💬 گفتگو با همراه", callback_data="chat_menu")],
        [InlineKeyboardButton("🧠 درمانگر درون", callback_data="therapy_menu")],
        [InlineKeyboardButton("🕰️ آیینه‌ی گذشته", callback_data="past_self_menu")],
        [InlineKeyboardButton("📊 پیش‌بینی فردا", callback_data="predict_menu")],
        [InlineKeyboardButton("📋 تاریخچه احساسات", callback_data="history_menu")],
        [InlineKeyboardButton("👤 ویرایش پروفایل", callback_data="profile_menu")]
    ]
    await message.reply_text("🏠 **منوی اصلی**", reply_markup=InlineKeyboardMarkup(keyboard))

async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"✅ chat_menu: user_id={query.from_user.id}")
    try:
        await query.message.delete()
    except:
        pass
    context.user_data['current_section'] = 'chat'
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
    await query.message.reply_text(
        "💬 **گفتگو با همراه**\n\nهر سوالی داری، بپرس.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def therapy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    await therapist.start_therapy(update, context)

async def past_self_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    await past_self.start_past_self(update, context)

async def predict_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    from app.handlers import predictor
    await predictor.predict_tomorrow(update, context)

async def history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    from app.handlers import history
    await history.full_history(update, context)

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    from app.handlers import profile_edit
    await profile_edit.show_profile(update, context)
