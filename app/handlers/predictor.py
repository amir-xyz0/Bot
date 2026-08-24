import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter
from datetime import datetime

logger = logging.getLogger(__name__)

async def predict_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
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

    if not message:
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            await message.reply_text(
                "❗ ثبت‌نام نکرده‌اید.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            db.close()
            return

        # دریافت احساسات اخیر
        mood_history = user.mood_history or []
        recent_moods = [h.get("mood") for h in mood_history[-14:] if h.get("mood")]
        
        if not recent_moods:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            await message.reply_text(
                "📊 **پیش‌بینی فردا**\n\n"
                "برای پیش‌بینی بهتر، حداقل چند روز احساساتت رو ثبت کن.\n"
                "از منوی اصلی می‌تونی احساساتت رو ثبت کنی.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            db.close()
            return

        # تحلیل احساسات
        good_count = recent_moods.count("good")
        bad_count = recent_moods.count("bad")
        neutral_count = recent_moods.count("neutral")
        
        mood_analysis = f"احساسات اخیر: {good_count} روز خوب، {bad_count} روز بد، {neutral_count} روز معمولی"
        
        # ساخت پرامپت پیش‌بینی
        prompt = f"""بر اساس احساسات اخیر کاربر، یک پیش‌بینی مثبت و امیدوارکننده برای فردا بده.

اطلاعات:
{ mood_analysis}

پیش‌بینی باید:
- کوتاه و دلنشین باشد (حداکثر ۳ پاراگراف)
- امیدوارکننده و انگیزشی باشد
- بر اساس احساسات اخیر، منطقی باشد
- با لحنی گرم و صمیمی نوشته شود

پیش‌بینی من برای فردا:"""

        result = call_openrouter(prompt, temperature=0.8, max_tokens=300, section="predictor")

        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        if result["success"]:
            await message.reply_text(
                f"📊 **پیش‌بینی فردا**\n\n{result['reply']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await message.reply_text(
                "📊 **پیش‌بینی فردا**\n\n"
                "متأسفم، الان نمی‌تونم پیش‌بینی کنم. لطفاً دوباره تلاش کن. ❤️",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        logger.error(f"❌ خطا در پیش‌بینی: {e}")
        await message.reply_text("❌ خطایی رخ داد.")
    finally:
        db.close()
