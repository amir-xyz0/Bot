import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    
    if not user:
        keyboard = [
            [InlineKeyboardButton("📝 شروع ثبت‌نام", callback_data="start_profile")]
        ]
        await update.message.reply_text(
            "👋 خوش آمدید!\n\n"
            "برای استفاده از ربات، ابتدا ثبت‌نام کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        db.close()
        return
    
    db.close()
    keyboard = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]
    await update.message.reply_text(
        f"👋 خوش برگشتی {user.preferred_name}!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
