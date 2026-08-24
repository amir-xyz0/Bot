import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from datetime import datetime

logger = logging.getLogger(__name__)

async def record_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    mood = query.data.split("_")[1]
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            if user.mood_history is None:
                user.mood_history = []
            user.mood_history.append({
                "mood": mood,
                "date": datetime.now().isoformat()
            })
            db.commit()
            logger.info(f"✅ احساسات کاربر {user_id} ثبت شد: {mood}")
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            await query.edit_message_text(
                f"✅ احساسات شما با موفقیت ثبت شد! 🌸\n\n"
                f"حالت امروزت: {mood}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("❗ کاربر یافت نشد.")
    except Exception as e:
        logger.error(f"❌ خطا در ثبت احساسات: {e}")
        await query.edit_message_text("❌ خطایی رخ داد.")
    finally:
        db.close()

async def full_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user or not user.mood_history or len(user.mood_history) == 0:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            await update.message.reply_text(
                "📭 **تاریخچه‌ای وجود ندارد.**\n\n"
                "هنوز احساساتی ثبت نکردی.\n"
                "از منوی اصلی می‌تونی احساساتت رو ثبت کنی.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            db.close()
            return
        
        history = user.mood_history[-30:]  # 30 مورد آخر
        text = "📋 **تاریخچه احساسات شما:**\n\n"
        for item in reversed(history):
            mood = item.get("mood", "نامشخص")
            date = item.get("date", "")
            if date:
                try:
                    dt = datetime.fromisoformat(date)
                    date_str = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    date_str = date
            else:
                date_str = "نامشخص"
            emoji = "😊" if mood == "good" else "😐" if mood == "neutral" else "😔" if mood == "bad" else "😢"
            text += f"{emoji} **{mood}** - {date_str}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"❌ خطا در نمایش تاریخچه: {e}")
        await update.message.reply_text("❌ خطایی رخ داد.")
    finally:
        db.close()
