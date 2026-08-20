import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اصلی"""
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(
            "📋 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 گفتگو با دستیار", callback_data="chat_menu")],
                [InlineKeyboardButton("🔮 پیش‌بینی روز", callback_data="predict_menu")],
                [InlineKeyboardButton("🕰️ خود گذشته", callback_data="past_self_menu")],
                [InlineKeyboardButton("🧠 درمانگر شناختی", callback_data="therapy_menu")],
                [InlineKeyboardButton("📊 تاریخچه احساسات", callback_data="history_menu")],
                [InlineKeyboardButton("👤 پروفایل", callback_data="profile_menu")]
            ])
        )
    else:
        await update.message.reply_text(
            "📋 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 گفتگو با دستیار", callback_data="chat_menu")],
                [InlineKeyboardButton("🔮 پیش‌بینی روز", callback_data="predict_menu")],
                [InlineKeyboardButton("🕰️ خود گذشته", callback_data="past_self_menu")],
                [InlineKeyboardButton("🧠 درمانگر شناختی", callback_data="therapy_menu")],
                [InlineKeyboardButton("📊 تاریخچه احساسات", callback_data="history_menu")],
                [InlineKeyboardButton("👤 پروفایل", callback_data="profile_menu")]
            ])
        )

async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به بخش گفتگو"""
    query = update.callback_query
    await query.answer()
    logger.info(f"✅ chat_menu: user_id={update.effective_user.id}")
    context.user_data['current_section'] = 'chat'
    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text(
        "💬 **بخش گفتگو با دستیار**\n\nهر سوالی دارید، بپرسید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ])
    )

async def predict_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به بخش پیش‌بینی روز"""
    query = update.callback_query
    await query.answer()
    logger.info(f"✅ predict_menu: user_id={update.effective_user.id}")
    from app.handlers import predictor
    await predictor.show_prediction(update, context)

async def past_self_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به بخش خود گذشته"""
    query = update.callback_query
    await query.answer()
    logger.info(f"✅ past_self_menu: user_id={update.effective_user.id}")
    from app.handlers import past_self
    await past_self.start_past_self(update, context)

async def therapy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به بخش درمانگر شناختی"""
    query = update.callback_query
    await query.answer()
    logger.info(f"✅ therapy_menu: user_id={update.effective_user.id}")
    from app.handlers import therapist
    await therapist.start_therapy(update, context)

async def history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به بخش تاریخچه احساسات"""
    query = update.callback_query
    await query.answer()
    logger.info(f"✅ history_menu: user_id={update.effective_user.id}")
    from app.handlers import history
    await history.show_history(update, context)

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به بخش پروفایل"""
    query = update.callback_query
    await query.answer()
    logger.info(f"✅ profile_menu: user_id={update.effective_user.id}")
    from app.handlers import profile_edit
    await profile_edit.show_profile(update, context)
