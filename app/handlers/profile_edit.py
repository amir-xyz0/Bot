import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        logger.info(f"👤 نمایش پروفایل برای user_id: {user_id}")
        
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(user_id=user_id).first()
        except Exception as e:
            logger.error(f"❌ خطا در دیتابیس: {e}")
            db.close()
            await update.message.reply_text("❌ خطا در اتصال به دیتابیس.")
            return
        
        if not user:
            db.close()
            await update.message.reply_text("❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
            return
        
        gender_map = {"male": "مرد", "female": "زن"}
        style_map = {"friendly": "دوستانه", "formal": "رسمی", "funny": "طنز", "calm": "آرام"}
        
        text = (
            f"👤 **پروفایل شما**\n\n"
            f"نام: {user.preferred_name}\n"
            f"جنسیت: {gender_map.get(user.gender, 'نامشخص')}\n"
            f"سن: {user.age}\n"
            f"لحن: {style_map.get(user.chat_style, 'نامشخص')}\n"
            f"اعلان صبح: {'✅ فعال' if user.morning_msg_enabled else '❌ غیرفعال'}\n"
            f"اعلان شب: {'✅ فعال' if user.night_msg_enabled else '❌ غیرفعال'}"
        )
        
        keyboard = [
            [InlineKeyboardButton("✏️ ویرایش نام", callback_data="edit_name")],
            [InlineKeyboardButton("🔄 تغییر جنسیت", callback_data="edit_gender")],
            [InlineKeyboardButton("🔄 تغییر سن", callback_data="edit_age")],
            [InlineKeyboardButton("🔄 تغییر لحن", callback_data="edit_style")],
            [InlineKeyboardButton("🔔 تغییر تنظیمات اعلان", callback_data="edit_notifications")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        
        db.close()
        
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            try:
                await query.message.delete()
            except:
                pass
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            
    except Exception as e:
        logger.error(f"❌ خطای ناشناخته در show_profile: {e}")
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
