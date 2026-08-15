from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.handlers.menu import main_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    
    if user:
        # کاربر قدیمی → مستقیم به منوی اصلی
        await main_menu(update, context)
    else:
        # کاربر جدید → ثبت‌نام
        keyboard = [
            [InlineKeyboardButton("🚀 شروع ثبت‌نام", callback_data="start_profile")]
        ]
        await update.message.reply_text(
            "🤖 **به دستیار همراهت خوش اومدی!**\n\n"
            "من اینجام تا روزت رو بهتر کنم.\n"
            "بیا پروفایل رو کامل کنیم تا بهتر بشناسمت.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    db.close()
