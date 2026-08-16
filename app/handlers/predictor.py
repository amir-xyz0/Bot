import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

async def show_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        try:
            await message.delete()
        except:
            pass
    else:
        message = update.message
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        await message.reply_text("❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        return
    
    mood_history = user.mood_history or []
    
    if len(mood_history) < 3:
        await message.reply_text(
            "📊 **داده‌ی کافی برای پیش‌بینی وجود ندارد.**\n\n"
            "لطفاً حداقل ۳ روز احساسات خود را ثبت کنید تا بتوانم الگوهای شما را شناسایی کنم.\n\n"
            "هر شب ساعت ۲۳ از شما می‌پرسم روزتان چطور بوده."
        )
        return
    
    recent = mood_history[-7:]
    good_days = sum(1 for h in recent if h.get("mood") == "good")
    bad_days = sum(1 for h in recent if h.get("mood") == "bad")
    
    trend = "صعودی 📈" if good_days > bad_days else "نزولی 📉" if bad_days > good_days else "متغیر 🔄"
    
    predictions = []
    if good_days >= 4:
        predictions.append("✅ انرژی خوبی خواهید داشت.")
        predictions.append("🌟 امروز روز مناسبی برای شروع کارهای جدید است.")
    elif bad_days >= 4:
        predictions.append("⚠️ ممکن است امروز احساس خستگی کنید.")
        predictions.append("💆 به خودتان استراحت بدهید.")
    else:
        predictions.append("🌿 روز متعادلی خواهید داشت.")
        predictions.append("📝 امروز برای برنامه‌ریزی روزهای آینده مناسب است.")
    
    extra_predictions = [
        "🤝 امروز با کسی آشنا می‌شوید که تأثیر مثبتی روی شما دارد.",
        "📚 امروز زمان خوبی برای خواندن یا یادگیری است.",
        "🎨 خلاقیت شما امروز در بالاترین سطح است.",
        "💪 امروز می‌توانید بر یک چالش قدیمی غلبه کنید.",
        "🌅 امروز از یک منظره یا لحظه‌ی ساده لذت خواهید برد."
    ]
    predictions.append(random.choice(extra_predictions))
    
    text = (
        f"🔮 **پیش‌بینی امروز**\n\n"
        f"📊 روند احساسات: {trend}\n"
        f"📅 روزهای خوب: {good_days} از ۷ روز\n\n"
        f"**پیش‌بینی‌ها:**\n"
        f"• {predictions[0]}\n"
        f"• {predictions[1]}\n"
        f"• {predictions[2] if len(predictions) > 2 else '🌟 روز خوبی در پیش دارید!'}\n\n"
        f"💡 این پیش‌بینی بر اساس {len(recent)} روز اخیر شماست."
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 پیش‌بینی فردا", callback_data="predict_tomorrow")],
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
    ]
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def predict_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # حذف پیام قبلی و نمایش دوباره
    try:
        await query.message.delete()
    except:
        pass
    await show_prediction(update, context)
