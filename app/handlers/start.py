from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.handlers.menu import main_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()

    # پاک کردن وضعیت قبلی
    context.user_data.clear()

    if user:
        await main_menu(update, context)
        return

    text = (
        "🤖 **به دستیار هوشمند خود خوش آمدید**\n\n"
        "من اینجا هستم تا به شما در مدیریت روزانه، یادآوری‌ها، "
        "گفتگو و ثبت احساسات کمک کنم.\n\n"
        "برای شروع، لطفاً ثبت‌نام را تکمیل کنید."
    )
    keyboard = [[InlineKeyboardButton("🚀 شروع ثبت‌نام", callback_data="start_profile")]]
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
