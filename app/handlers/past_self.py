import logging
import json
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

async def start_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع گفتگو با خود گذشته"""
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
    
    # بررسی وجود داده‌های کافی
    mood_history = user.mood_history or []
    if len(mood_history) < 5:
        await message.reply_text(
            "📊 **داده‌ی کافی برای شبیه‌سازی خود گذشته وجود ندارد.**\n\n"
            "لطفاً حداقل ۵ روز احساسات خود را ثبت کنید تا بتوانم نسخه‌ی گذشته‌ی شما را بسازم.\n"
            "هر شب ساعت ۲۳ از شما می‌پرسم روزتان چطور بوده."
        )
        return
    
    context.user_data['past_self_mode'] = True
    
    # ارسال پیام شروع
    text = (
        "🕰️ **گفتگو با خود گذشته**\n\n"
        "من نسخه‌ی گذشته‌ی شما را شبیه‌سازی کرده‌ام. "
        "حالا می‌توانید با او گفتگو کنید و ببینید چقدر تغییر کرده‌اید.\n\n"
        "هر سوالی دارید، بپرسید. مثلاً:\n"
        "• «۶ ماه پیش در این شرایط چیکار می‌کردی؟»\n"
        "• «چرا فلان تصمیم رو گرفتی؟»\n"
        "• «حالا چطور به گذشته نگاه می‌کنی؟»\n\n"
        "برای پایان گفتگو، دکمه‌ی زیر را بزنید."
    )
    
    keyboard = [[InlineKeyboardButton("🔚 پایان گفتگو", callback_data="end_past_self")]]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def chat_with_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مکالمه با خود گذشته"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    if not context.user_data.get('past_self_mode'):
        return
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        await update.message.reply_text("❗ شما ثبت‌نام نکرده‌اید.")
        return
    
    # ساخت پروفایل از داده‌های کاربر
    mood_history = user.mood_history or []
    recent_moods = [h.get("mood") for h in mood_history[-7:] if h.get("mood")]
    mood_summary = "خوب" if recent_moods.count("good") > len(recent_moods)/2 else "معمولی و متغیر"
    
    prompt = f"""شما نسخه‌ی گذشته‌ی یک کاربر هستید. کاربر در حال گفتگو با شماست تا ببیند چقدر تغییر کرده است.

اطلاعات کاربر (از گذشته):
- نام: {user.preferred_name}
- جنسیت: {'مرد' if user.gender == 'male' else 'زن'}
- سن: {user.age}
- سبک لحن: {user.chat_style}
- وضعیت احساسی اخیر: {mood_summary}

شما باید با لحن و شخصیت کاربر (از گذشته) پاسخ دهید. پاسخ‌ها باید طبیعی، انسانی و صمیمی باشد.
می‌توانید به تصمیمات گذشته، احساسات و تجربیات اشاره کنید.

پیام کاربر: {user_message}

پاسخ خود را به‌عنوان «خود گذشته» بنویسید:
"""

    try:
        url = f"{config.OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.9,
            "max_tokens": 300
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json()
        
        if response.status_code == 200:
            reply = response_data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                # اضافه کردن امضای "خود گذشته"
                await update.message.reply_text(f"🕰️ **خود گذشته:**\n\n{reply}")
                return
    except Exception as e:
        logger.error(f"خطا در past_self: {e}")
    
    # پاسخ پیش‌فرض در صورت خطا
    await update.message.reply_text(
        "🕰️ **خود گذشته:**\n\n"
        "متأسفم، الان نمی‌تونم خوب فکر کنم. شاید بعداً بهتر بتونم کمک کنم."
    )

async def end_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پایان گفتگو با خود گذشته"""
    query = update.callback_query
    await query.answer()
    context.user_data['past_self_mode'] = False
    
    try:
        await query.message.delete()
    except:
        pass
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
    await query.message.reply_text(
        "✅ **گفتگو با خود گذشته به پایان رسید.**\n\n"
        "هر وقت خواستید دوباره گفتگو کنید، از منو انتخاب کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
