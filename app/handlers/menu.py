import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی اصلی با چیدمان دو ستونه"""
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        await query.message.reply_text(
            "🌿 **به خانه خوش آمدی!** 🌿\n\n"
            "از میان گزینه‌های زیر، مسیر امروزت را انتخاب کن...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 گفتگو با همراه", callback_data="chat_menu"),
                 InlineKeyboardButton("🔮 طالع‌روزانه", callback_data="predict_menu")],
                [InlineKeyboardButton("🕰️ آیینه‌ی گذشته", callback_data="past_self_menu"),
                 InlineKeyboardButton("🧠 درمانگر درون", callback_data="therapy_menu")],
                [InlineKeyboardButton("📊 دفترچه‌ی احساسات", callback_data="history_menu"),
                 InlineKeyboardButton("👤 پروفایل من", callback_data="profile_menu")]
            ])
        )
    else:
        await update.message.reply_text(
            "🌿 **به خانه خوش آمدی!** 🌿\n\n"
            "از میان گزینه‌های زیر، مسیر امروزت را انتخاب کن...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 گفتگو با همراه", callback_data="chat_menu"),
                 InlineKeyboardButton("🔮 طالع‌روزانه", callback_data="predict_menu")],
                [InlineKeyboardButton("🕰️ آیینه‌ی گذشته", callback_data="past_self_menu"),
                 InlineKeyboardButton("🧠 درمانگر درون", callback_data="therapy_menu")],
                [InlineKeyboardButton("📊 دفترچه‌ی احساسات", callback_data="history_menu"),
                 InlineKeyboardButton("👤 پروفایل من", callback_data="profile_menu")]
            ])
        )

async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"✅ chat_menu: user_id={update.effective_user.id}")
    context.user_data['current_section'] = 'chat'
    try:
        await query.message.delete()
    except:
        pass
    await query.message.reply_text(
        "💬 **گفتگو با همراه**\n\n"
        "هر چیزی که در دلت هست، با من در میان بگذار.\n"
        "من اینجام تا گوش کنم، همراهی کنم و اگر توانی داشته باشم، راهی نشانت دهم.\n\n"
        "🌱 **چه می‌خواهی بگویی؟**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
        ])
    )

async def predict_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from app.handlers import predictor
    await predictor.show_prediction(update, context)

async def past_self_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from app.handlers import past_self
    await past_self.start_past_self(update, context)

async def therapy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from app.handlers import therapist
    await therapist.start_therapy(update, context)

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
