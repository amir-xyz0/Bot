import logging
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

# سوالات استاندارد CBT
THERAPY_QUESTIONS = {
    "start": "سلام! من اینجام تا بهت کمک کنم افکارت رو بهتر بشناسی.\n\nامروز چه احساسی داری؟ می‌تونی با یک کلمه یا یک جمله توصیفش کنی.",
    "identify": "چه فکری باعث این احساس شده؟",
    "challenge": "چه مدرکی داری که این فکر درسته؟ آیا ممکنه راه‌های دیگه‌ای هم برای نگاه به این موضوع وجود داشته باشه؟",
    "reframe": "حالا بیا یه فکر جایگزین و منطقی‌تر پیدا کنیم. چه فکری می‌تونه آرام‌ت کنه؟",
    "action": "امروز چیکار می‌تونی بکنی که این فکر رو کمتر کنی؟",
}

async def start_therapy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع جلسه‌ی درمانگری"""
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
    
    context.user_data['therapy_mode'] = True
    context.user_data['therapy_step'] = 'start'
    
    keyboard = [[InlineKeyboardButton("🔚 پایان جلسه", callback_data="end_therapy")]]
    await message.reply_text(
        f"🧠 **درمانگر شناختی**\n\n{THERAPY_QUESTIONS['start']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def chat_with_therapist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مکالمه با درمانگر"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    if not context.user_data.get('therapy_mode'):
        return
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        await update.message.reply_text("❗ شما ثبت‌نام نکرده‌اید.")
        return
    
    step = context.user_data.get('therapy_step', 'start')
    
    # ساخت پرامپت برای OpenRouter
    prompt = f"""تو یک درمانگر شناختی (CBT) هستی. با کاربری گفتگو می‌کنی که به دنبال کمک برای مدیریت افکار و احساساتش است.

مرحله‌ی فعلی: {step}
سوال استاندارد برای این مرحله: {THERAPY_QUESTIONS.get(step, '')}

اطلاعات کاربر:
- نام: {user.preferred_name}
- سن: {user.age}
- سبک لحن: {user.chat_style}

پیام کاربر: {user_message}

وظیفه‌ات:
1. پاسخ را با همدلی و گرمی بده.
2. در پایان، سوال بعدی را بپرس (طبق مرحله‌ی بعد).
3. اگر کاربر پاسخش کامل بود، به مرحله‌ی بعد برو.

پاسخ خود را به‌عنوان یک درمانگر بنویس:
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
            "temperature": 0.8,
            "max_tokens": 350
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json()
        
        if response.status_code == 200:
            reply = response_data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                # پیشرفت به مرحله‌ی بعد
                steps = ['start', 'identify', 'challenge', 'reframe', 'action']
                current_idx = steps.index(step) if step in steps else 0
                if current_idx < len(steps) - 1:
                    context.user_data['therapy_step'] = steps[current_idx + 1]
                
                keyboard = [[InlineKeyboardButton("🔚 پایان جلسه", callback_data="end_therapy")]]
                await update.message.reply_text(
                    f"🧠 **درمانگر:**\n\n{reply}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
    except Exception as e:
        logger.error(f"خطا در therapist: {e}")
    
    # پاسخ پیش‌فرض
    await update.message.reply_text(
        "🧠 **درمانگر:**\n\n"
        "متأسفم، الان کمی گیج شدم. بیا از اول شروع کنیم.\n"
        f"{THERAPY_QUESTIONS['start']}"
    )

async def end_therapy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پایان جلسه‌ی درمانگری"""
    query = update.callback_query
    await query.answer()
    context.user_data['therapy_mode'] = False
    context.user_data['therapy_step'] = 'start'
    
    try:
        await query.message.delete()
    except:
        pass
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
    await query.message.reply_text(
        "✅ **جلسه‌ی درمانگری به پایان رسید.**\n\n"
        "امیدوارم امروز کمی بهتر شده باشید. هر وقت نیاز داشتید، من اینجام.",
        reply_markup=InlineKeyboardMarkup(keyboard)
  )
