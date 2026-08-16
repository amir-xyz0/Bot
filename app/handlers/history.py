from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from datetime import datetime

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # حذف پیام قبلی (اگر از callback آمده باشد)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
    
    # ارسال پیام لودینگ
    loading_msg = await update.effective_message.reply_text("⏳ در حال بارگذاری تاریخچه...")
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        await loading_msg.delete()
        await update.effective_message.reply_text("❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        return
    
    history = user.mood_history or []
    
    if not history:
        await loading_msg.delete()
        text = (
            "📭 **هنوز هیچ احساسی ثبت نکردی!**\n\n"
            "هر شب ساعت ۲۳، ازت می‌پرسم روزت چطور بوده.\n"
            "با ثبت احساساتت، می‌تونم بهتر کمکت کنم."
        )
        keyboard = [[InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]]
        await update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    recent = history[-14:]
    mood_count = {"good": 0, "normal": 0, "bad": 0}
    for h in recent:
        mood = h.get("mood", "normal")
        mood_count[mood] = mood_count.get(mood, 0) + 1
    
    total = len(recent)
    good_pct = (mood_count["good"] / total * 100) if total > 0 else 0
    bad_pct = (mood_count["bad"] / total * 100) if total > 0 else 0
    
    analysis = ""
    if good_pct > 70:
        analysis = "🌟 **روحیه‌ات عالیه!** ادامه بده. امروز هم کارهای خوبی که دوست داری رو انجام بده."
    elif good_pct > 50:
        analysis = "🌿 **روحیه‌ات نسبتاً خوبه.** روزهای خوب و بد داری. سعی کن روزهای خوب رو بیشتر کنی."
    elif bad_pct > 60:
        analysis = "💔 **این روزها سخت بوده.** تنها نیستی. یه پیاده‌روی برو، با یه دوست صحبت کن، یا به موسیقی گوش بده. به خودت سخت نگیر."
    else:
        analysis = "🌈 **احساساتت متعادله.** برای بهبود روحیه، هر روز به کارهای خوبی که انجام دادی فکر کن."
    
    history_text = "📊 **۱۴ روز اخیر:**\n\n"
    for h in recent[-7:]:
        date = datetime.fromisoformat(h["date"]).strftime("%Y-%m-%d")
        mood = h.get("mood", "normal")
        emoji = "😊" if mood == "good" else "😐" if mood == "normal" else "😔"
        history_text += f"• {date}: {emoji}\n"
    
    full_text = history_text + f"\n**تحلیل:**\n{analysis}"
    
    keyboard = [
        [InlineKeyboardButton("📋 تاریخچه کامل", callback_data="full_history")],
        [InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]
    ]
    
    # ✅ حذف پیام لودینگ قبل از ارسال پاسخ نهایی
    await loading_msg.delete()
    
    await update.effective_message.reply_text(full_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def full_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        await query.message.delete()
    except:
        pass
    
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user or not user.mood_history:
        await query.message.reply_text("📭 تاریخچه‌ای وجود ندارد.")
        return
    
    history = user.mood_history[-30:]
    text = "📋 **تاریخچه کامل (۳۰ روز اخیر):**\n\n"
    for h in history:
        date = datetime.fromisoformat(h["date"]).strftime("%Y-%m-%d")
        mood = h.get("mood", "normal")
        emoji = "😊" if mood == "good" else "😐" if mood == "normal" else "😔"
        text += f"• {date}: {emoji}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]]
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def record_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mood = query.data.replace("mood_", "")
    
    user_id = update.effective_user.id
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
    
    try:
        await query.message.delete()
    except:
        pass
    
    emoji = "😊" if mood == "good" else "😐" if mood == "normal" else "😔"
    await query.message.reply_text(
        f"✅ احساس امروز ثبت شد!\n\n"
        f"حالت: {emoji}\n"
        f"شب بخیر و خواب آرام 🌙"
    )
