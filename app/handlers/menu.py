import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.handlers import past_self, therapist

logger = logging.getLogger(__name__)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی (با حذف پیام قبلی)"""
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
        [InlineKeyboardButton("💬 گفتگوی همراه", callback_data="chat_menu"),
         InlineKeyboardButton("🧠 مشاوره", callback_data="therapy_menu")],
        [InlineKeyboardButton("🕰️ آیینه‌ی گذشته", callback_data="past_self_menu"),
         InlineKeyboardButton("📊 پیش‌بینی فردا", callback_data="predict_menu")],
        [InlineKeyboardButton("📋 تاریخچه احساسات", callback_data="history_menu"),
         InlineKeyboardButton("👤 پروفایل من", callback_data="profile_menu")]
    ]
    
    text = (
        "🏠 **خانه**\n\n"
        "به ربات همراه و مشاوره شخصی خود خوش آمدی. 🌸\n\n"
        "اینجا می‌تونی:\n"
        "• با **همراه هوشمند** خودت گفتگو کنی\n"
        "• از **مشاوره‌های عمیق** بهره‌مند بشی\n"
        "• با **گذشته‌ات** ارتباط بگیری و ازش یاد بگیری\n"
        "• احساساتت رو **ثبت** کنی و روندش رو ببینی\n"
        "• و خیلی چیزهای دیگه...\n\n"
        "✨ هر روزت بهتر از دیروز ❤️"
    )
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def main_menu_keep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی (بدون حذف پیام قبلی - مخصوص پیام سلامت)"""
    query = update.callback_query
    await query.answer()
    
    # 🔥 پیام قبلی رو حذف نمیکنیم (فقط منو رو ارسال میکنیم)
    message = query.message
    
    keyboard = [
        [InlineKeyboardButton("💬 گفتگوی همراه", callback_data="chat_menu"),
         InlineKeyboardButton("🧠 مشاوره", callback_data="therapy_menu")],
        [InlineKeyboardButton("🕰️ آیینه‌ی گذشته", callback_data="past_self_menu"),
         InlineKeyboardButton("📊 پیش‌بینی فردا", callback_data="predict_menu")],
        [InlineKeyboardButton("📋 تاریخچه احساسات", callback_data="history_menu"),
         InlineKeyboardButton("👤 پروفایل من", callback_data="profile_menu")]
    ]
    
    text = (
        "🏠 **خانه**\n\n"
        "به ربات همراه و مشاوره شخصی خود خوش آمدی. 🌸\n\n"
        "اینجا می‌تونی:\n"
        "• با **همراه هوشمند** خودت گفتگو کنی\n"
        "• از **مشاوره‌های عمیق** بهره‌مند بشی\n"
        "• با **گذشته‌ات** ارتباط بگیری و ازش یاد بگیری\n"
        "• احساساتت رو **ثبت** کنی و روندش رو ببینی\n"
        "• و خیلی چیزهای دیگه...\n\n"
        "✨ هر روزت بهتر از دیروز ❤️"
    )
    
    # ارسال منو به صورت پیام جدید (بدون حذف پیام سلامت)
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    
    context.user_data['current_section'] = 'chat'
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text(
        "💬 **گفتگوی همراه**\n\n"
        "هر سوالی داری، هر موضوعی که دلت می‌خواد درباره‌ش حرف بزنی، بپرس.\n"
        "من اینجام تا همراه و هم‌نشین خوبی برات باشم. 🌸",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def therapy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await therapist.start_therapy(update, context)

async def past_self_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
