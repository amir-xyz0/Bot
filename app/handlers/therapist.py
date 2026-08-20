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
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()

    if not user:
        await message.reply_text("❗ ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        return

    context.user_data['therapy_mode'] = True
    context.user_data['therapy_step'] = 'start'

    keyboard = [[InlineKeyboardButton("🔚 پایان جلسه", callback_data="end_therapy")]]
    await message.reply_text(
        f"🧠 **درمانگر درون**\n\n{THERAPY_QUESTIONS['start']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def chat_with_therapist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if not context.user_data.get('therapy_mode'):
        return

    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()

    if not user:
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید.")
        return

    step = context.user_data.get('therapy_step', 'start')

    # ============================================================
    # پرامپت اختصاصی درمانگر – فلسفی، عمیق و همدلانه
    # ============================================================
    prompt = f"""تو یک درمانگر شناختی-رفتاری با سبک «فلسفی و همدلانه» هستی.

ویژگی‌های تو:
- لحنت گرم، عمیق و انسانی است
- مانند یک حکیم یا مشاور بزرگ صحبت می‌کنی
- از جملات تأمل‌برانگیز و پرسش‌های سقراطی استفاده می‌کنی
- هرگز قضاوت نمی‌کنی، فقط همراهی می‌کنی

مرحله فعلی جلسه: {step}
سوال استاندارد این مرحله: {THERAPY_QUESTIONS.get(step, '')}

اطلاعات کاربر:
- نام: {user.preferred_name}
- سن: {user.age}

پیام کاربر: {user_message}

وظیفه‌ات:
۱. با همدلی عمیق پاسخ بده.
۲. پاسخ باید حس کند که یک انسان واقعی با او حرف می‌زند.
۳. در پایان، سوال بعدی را به‌صورت طبیعی بپرس.
۴. از جملات فلسفی و الهام‌بخش استفاده کن.

پاسخ خود را به‌عنوان یک درمانگر بنویس:"""

    result = call_openrouter(prompt, temperature=0.75, max_tokens=500, section="therapist")

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
        await update.message.reply_text(
            f"🧠 **درمانگر:**\n\nمتأسفم، الان نمی‌تونم خوب فکر کنم. بیا از اول شروع کنیم.\n"
            f"{THERAPY_QUESTIONS['start']}"
        )

async def end_therapy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['therapy_mode'] = False
    context.user_data['therapy_step'] = 'start'

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text(
        "🌿 **جلسه‌ی درمانگری به پایان رسید.**\n\n"
        "از اینکه اجازه دادی کنارت باشم سپاسگزارم.\n"
        "هر زمان که نیاز داشتی، من اینجام.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
