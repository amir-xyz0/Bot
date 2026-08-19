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
    "start": "سلام! من اینجام تا بهت کمک کنم افکارت رو بهتر بشناسی.\n\nامروز چه احساسی داری؟",
    "identify": "چه فکری باعث این احساس شده؟",
    "challenge": "چه مدرکی داری که این فکر درسته؟ آیا ممکنه راه‌های دیگه‌ای هم وجود داشته باشه؟",
    "reframe": "حالا بیا یه فکر جایگزین و منطقی‌تر پیدا کنیم.",
    "action": "امروز چیکار می‌تونی بکنی که این فکر رو کمتر کنی؟"
}

async def start_therapy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع جلسه‌ی درمانگری"""
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

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except:
        user = None

    if not user:
        await message.reply_text("❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        db.close()
        return

    context.user_data['therapy_mode'] = True
    context.user_data['therapy_step'] = 'start'

    keyboard = [[InlineKeyboardButton("🔚 پایان جلسه", callback_data="end_therapy")]]
    await message.reply_text(
        f"🧠 **درمانگر شناختی**\n\n{THERAPY_QUESTIONS['start']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    db.close()

async def chat_with_therapist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مکالمه با درمانگر"""
    user_id = update.effective_user.id
    user_message = update.message.text

    if not context.user_data.get('therapy_mode'):
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except:
        user = None

    if not user:
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید.")
        db.close()
        return

    step = context.user_data.get('therapy_step', 'start')

    prompt = f"""تو یک درمانگر شناختی (CBT) هستی که با کاربری همدلانه و حرفه‌ای گفتگو می‌کند.

مرحله فعلی: {step}
سوال استاندارد این مرحله: {THERAPY_QUESTIONS.get(step, '')}

نام کاربر: {user.preferred_name}
سن: {user.age}
لحن موردعلاقه: {user.chat_style}

پیام کاربر: {user_message}

وظیفه‌ات:
۱. با همدلی، گرمی و احترام پاسخ بده.
۲. در پایان پاسخ، سوال بعدی را بپرس (طبق مرحله‌ی بعد).
۳. اگر کاربر پاسخش کامل بود، به مرحله‌ی بعد برو.

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
            "temperature": 0.7,
            "max_tokens": 400
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
                db.close()
                return
    except Exception as e:
        logger.error(f"خطا در therapist: {e}")

    await update.message.reply_text(
        "🧠 **درمانگر:**\n\nمتأسفم، الان کمی گیج شدم. بیا از اول شروع کنیم."
    )
    db.close()

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
        "امیدوارم امروز کمی بهتر شده باشید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
