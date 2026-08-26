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
    
    logger.info(f"📝 ثبت احساسات: user_id={user_id}, mood={mood}")
    
    mood_map = {
        "good": "😊 خوب",
        "neutral": "😐 معمولی",
        "bad": "😔 بد"
    }
    mood_text = mood_map.get(mood, mood)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            await query.edit_message_text("❗ کاربر یافت نشد.")
            db.close()
            return
        
        if user.mood_history is None:
            user.mood_history = []
        
        # اضافه کردن احساسات جدید
        new_entry = {
            "mood": mood,
            "date": datetime.now().isoformat()
        }
        user.mood_history.append(new_entry)
        db.commit()
        
        logger.info(f"✅ احساسات کاربر {user_id} ذخیره شد. تعداد کل: {len(user.mood_history)}")
        
        # حذف پیام دکمه‌های انتخاب احساسات
        try:
            await query.message.delete()
            logger.info("✅ پیام دکمه‌های احساسات حذف شد.")
        except Exception as e:
            logger.warning(f"⚠️ خطا در حذف پیام: {e}")
        
        # ارسال پیام تأیید با دکمه بازگشت
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await query.message.reply_text(
            f"✅ احساسات شما با موفقیت ثبت شد! 🌸\n\n"
            f"حالت امروزت: {mood_text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"❌ خطا در ثبت احساسات: {e}")
        await query.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کن.")
    finally:
        db.close()

async def full_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"📋 نمایش تاریخچه: user_id={user_id}")
    
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        message = query.message
    else:
        message = update.message
    
    if not message:
        return
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            await message.reply_text(
                "❗ کاربر یافت نشد.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            db.close()
            return
        
        if not user.mood_history or len(user.mood_history) == 0:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            text = (
                "📭 **تاریخچه‌ای وجود ندارد.**\n\n"
                "هنوز احساساتی ثبت نکردی.\n"
                "از منوی اصلی می‌تونی احساساتت رو ثبت کنی."
            )
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            db.close()
            return
        
        logger.info(f"📊 تعداد احساسات ثبت‌شده: {len(user.mood_history)}")
        
        history = user.mood_history[-30:]
        text = "📋 **تاریخچه احساسات شما:**\n\n"
        mood_emoji = {
            "good": "😊",
            "happy": "😄",
            "neutral": "😐",
            "bad": "😔",
            "sad": "😢",
            "angry": "😡",
            "excited": "🤩",
            "tired": "😴",
            "anxious": "😰"
        }
        
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
            
            emoji = mood_emoji.get(mood, "🤔")
            text += f"{emoji} **{mood}** - {date_str}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"❌ خطا در نمایش تاریخچه: {e}")
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کن.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        db.close()
