from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from datetime import datetime, timedelta
import json

async def record_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت احساس از طریق اعلان شب"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    mood = query.data.replace("mood_", "")
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    if user:
        history = user.mood_history or []
        history.append({
            "date": datetime.now().isoformat(),
            "mood": mood,
            "note": ""
        })
        user.mood_history = history
        db.commit()
    db.close()
    
    await query.edit_message_text(
        f"✅ احساس امروز شما ثبت شد!\n\n"
        f"حالت: {'😊 خوب' if mood == 'good' else '😐 معمولی' if mood == 'normal' else '😔 بد'}"
    )

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تاریخچه و تحلیل"""
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user or not user.mood_history:
        text = "📭 **هنوز هیچ احساسی ثبت نکردی!**\n\nشب‌ها وقتی پیام شب بخیر می‌رسد، ازت می‌پرسم روزت چطور بوده. با ثبت احساساتت، می‌تونم بهتر کمکت کنم."
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    history = user.mood_history[-14:]  # ۱۴ روز اخیر
    
    # تحلیل احساسات
    mood_count = {"good": 0, "normal": 0, "bad": 0}
    for h in history:
        mood = h.get("mood", "normal")
        mood_count[mood] = mood_count.get(mood, 0) + 1
    
    total = len(history)
    good_percent = (mood_count["good"] / total * 100) if total > 0 else 0
    bad_percent = (mood_count["bad"] / total * 100) if total > 0 else 0
    
    # تولید تحلیل
    analysis = ""
    if good_percent > 70:
        analysis = "🌟 وضعیت روحی شما عالی است! این روند را حفظ کنید. پیشنهاد می‌کنم امروز هم کارهای خوبی که باعث شادی‌تان می‌شود را ادامه دهید."
    elif good_percent > 50:
        analysis = "🌿 روحیه‌تان نسبتاً خوب است. روزهای خوب و بدی دارید. سعی کنید روزهای خوب را بیشتر کنید."
    elif bad_percent > 60:
        analysis = "💔 این روزها سخت بوده. یادتان باشد که تنها نیستید. پیشنهاد می‌کنم امروز یک پیاده‌روی کوتاه بروید، با یک دوست صحبت کنید، یا به موسیقی آرامش‌بخش گوش دهید. به خودتان سخت نگیرید."
    else:
        analysis = "🌈 احساسات شما متعادل است. برای بهبود روحیه، سعی کنید هر روز چند دقیقه به کارهای خوبی که انجام داده‌اید فکر کنید."
    
    # نمایش تاریخچه
    history_text = "📊 **تاریخچه احساسات (۱۴ روز اخیر):**\n\n"
    for h in history[-7:]:
        date = datetime.fromisoformat(h["date"]).strftime("%Y-%m-%d")
        mood = h.get("mood", "normal")
        mood_emoji = "😊" if mood == "good" else "😐" if mood == "normal" else "😔"
        history_text += f"• {date}: {mood_emoji}\n"
    
    full_text = history_text + f"\n**تحلیل:**\n{analysis}"
    
    keyboard = [
        [InlineKeyboardButton("📋 تاریخچه کامل", callback_data="full_history")],
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
    ]
    
    await update.message.reply_text(full_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def full_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user or not user.mood_history:
        await query.edit_message_text("📭 تاریخچه‌ای وجود ندارد.")
        return
    
    history = user.mood_history[-30:]
    text = "📋 **تاریخچه کامل (۳۰ روز اخیر):**\n\n"
    for h in history:
        date = datetime.fromisoformat(h["date"]).strftime("%Y-%m-%d")
        mood = h.get("mood", "normal")
        mood_emoji = "😊" if mood == "good" else "😐" if mood == "normal" else "😔"
        text += f"• {date}: {mood_emoji}\n"
    
    text += f"\n🔙 بازگشت به منو"
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ])
    )
