from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    context.user_data.clear()
    
    if user:
        from app.handlers.menu import main_menu
        await main_menu(update, context)
        return
    
    # ⭐ صفحه خوش‌آمدگویی مثل عکس (قبل از استارت)
    text = (
        "🤖 **دستیار هوشمند**\n"
        "ربات\n\n"
        "---\n\n"
        "**این ربات چه می‌کند؟**\n\n"
        "ربات دستیار هوشمند برای همراهی شما در زندگی روزمره\n\n"
        "• گفتگو با دستیار هوشمند\n"
        "• تنظیم یادآوری‌های روزانه\n"
        "• ثبت و تحلیل احساسات\n"
        "• مدیریت پروفایل شخصی\n\n"
        "---\n\n"
        "**شروع ربات**"
    )
    keyboard = [[InlineKeyboardButton("🚀 شروع ربات", callback_data="start_profile")]]
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
