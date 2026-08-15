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
        await main_menu(update, context)
    else:
        keyboard = [[InlineKeyboardButton("شروع ثبت‌نام", callback_data="start_profile")]]
        await update.message.reply_text(
            "به دستیار همراه خود خوش آمدید.\nلطفاً برای ادامه، ثبت‌نام را تکمیل کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    db.close()
