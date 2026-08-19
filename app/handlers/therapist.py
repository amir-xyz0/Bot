import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter

logger = logging.getLogger(__name__)

THERAPY_QUESTIONS = {
    "start": "سلام! من اینجام تا بهت کمک کنم افکارت رو بهتر بشناسی.\n\nامروز چه احساسی داری؟",
    "identify": "چه فکری باعث این احساس شده؟",
    "challenge": "چه مدرکی داری که این فکر درسته؟ آیا ممکنه راه‌های دیگه‌ای هم وجود داشته باشه؟",
    "reframe": "حالا بیا یه فکر جایگزین و منطقی‌تر پیدا کنیم.",
    "action": "امروز چیکار می‌تونی بکنی که این فکر رو کمتر کنی؟"
}

# ============================================================
# ۱. شروع جلسه درمانگری
# ============================================================
async def start_therapy(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ============================================================
# ۲. پردازش مکالمه با درمانگر (با تابع کمکی)
# ============================================================
async def chat_with_therapist(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

پاسخ خود را به‌عنوان یک درمانگر بنویس:"""

    db.close()

    result = call_openrouter(prompt, temperature=0.7, max_tokens=400)
    
    if result["success"]:
        steps = ['start', 'identify', 'challenge', 'reframe', 'action']
        current_idx = steps.index(step) if step in steps else 0
        if current_idx < len(steps) - 1:
            context.user_data['therapy_step'] = steps[current_idx + 1]

        keyboard = [[InlineKeyboardButton("🔚 پایان جلسه", callback_data="end_therapy")]]
        await update.message.reply_text(
            f"🧠 **درمانگر:**\n\n{result['reply']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(f"🧠 **درمانگر:**\n\nمتأسفم، الان کمی گیج شدم. (خطا: {result['error']})")

# ============================================================
# ۳. پایان جلسه درمانگری
# ============================================================
async def end_therapy(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "✅ **جلسه‌ی درمانگری به پایان رسید.**\n\nامیدوارم امروز کمی بهتر شده باشید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
