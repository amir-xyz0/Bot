from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
import json
from datetime import datetime

async def record_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # کاربر با /mood خوب یا /mood بد ثبت می‌کنه
    user_id = update.effective_user.id
    mood = context.args[0] if context.args else "خوب"
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        await update.message.reply_text("❌ اول /start رو بزن!")
        db.close()
        return
    
    history = user.mood_history or []
    history.append({
        "date": datetime.now().isoformat(),
        "mood": mood,
        "note": " ".join(context.args[1:]) if len(context.args) > 1 else ""
    })
    user.mood_history = history
    db.commit()
    db.close()
    
    await update.message.reply_text(f"✅ حالت امروز {mood} ثبت شد! 🙏")

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user or not user.mood_history:
        await update.message.reply_text("📭 هنوز هیچ احساسی ثبت نکردی!\nبا دستور /mood خوب یا /mood بد حالت رو ثبت کن.")
        return
    
    history = user.mood_history[-7:]  # ۷ روز اخیر
    text = "📊 **تاریخچه‌ی ۷ روز اخیر:**\n\n"
    
    mood_count = {"خوب": 0, "بد": 0, "معمولی": 0}
    for h in history:
        mood = h.get("mood", "معمولی")
        mood_count[mood] = mood_count.get(mood, 0) + 1
        date = datetime.fromisoformat(h["date"]).strftime("%Y-%m-%d")
        note = h.get("note", "")
        text += f"• {date}: {mood} {note}\n"
    
    text += f"\n📈 **تحلیل:**\n"
    total = len(history)
    good_percent = (mood_count["خوب"] / total * 100) if total > 0 else 0
    
    if good_percent > 60:
        text += "🌟 این روزها روحیه‌ات عالیه! ادامه بده!"
    elif good_percent > 40:
        text += "🌿 روزهای خوب و بد رو داری. به خودت فرصت بده."
    else:
        text += "💪 این روزها سخت بوده. یادت باشه تنها نیستی، من اینجام."
    
    keyboard = [
        [InlineKeyboardButton("📝 ثبت احساس جدید", callback_data="record_mood")],
        [InlineKeyboardButton("📋 تاریخچه کامل", callback_data="full_history")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def full_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user or not user.mood_history:
        await query.edit_message_text("📭 هیچ تاریخی وجود نداره!")
        return
    
    all_history = user.mood_history
    text = "📋 **تاریخچه‌ی کامل:**\n\n"
    for h in all_history[-20:]:  # آخرین ۲۰ مورد
        date = datetime.fromisoformat(h["date"]).strftime("%Y-%m-%d %H:%M")
        mood = h.get("mood", "معمولی")
        note = h.get("note", "")
        text += f"• {date}: {mood} {note}\n"
    
    await query.edit_message_text(text)
