import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter

logger = logging.getLogger(__name__)

# سوالات راهنما برای درمانگر (اختیاری)
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
    # پرامپت اختصاصی درمانگر – همدلانه، فلسفی و مشاوره‌ای
    # ============================================================
    prompt = f"""تو یک درمانگر شناختی-رفتاری (CBT) با سبک «همدلانه و فلسفی» هستی. 
تو با کاربری گفتگو می‌کنی که به دنبال درک بهتر احساسات و افکار خود است.

ویژگی‌های تو:
- لحن گرم، صمیمی و انسانی
- عمیق و تأمل‌برانگیز
- پرسش‌های سقراطی و کاوشگر
- همدلی عمیق بدون قضاوت

مرحله فعلی جلسه: {step}
سوال استاندارد این مرحله: {THERAPY_QUESTIONS.get(step, '')}

اطلاعات کاربر:
- نام: {user.preferred_name}
- سن: {user.age}
- لحن موردعلاقه‌اش: {user.chat_style}

پیام کاربر: {user_message}

وظیفه‌ات:
۱. با همدلی و احترام عمیق پاسخ بده.
۲. پاسخ باید حس کند که یک انسان واقعی با او حرف می‌زند، نه یک ربات.
۳. در پایان پاسخ، سوال بعدی را به‌صورت طبیعی بپرس.
۴. از جملات فلسفی و الهام‌بخش استفاده کن (نه خشک و تکنیکی).

پاسخ خود را به‌عنوان یک درمانگر بنویس (بدون مقدمه‌چینی اضافی):"""

    # ============================================================
    # ارسال به OpenRouter
    # ============================================================
    result = call_openrouter(prompt, temperature=0.75, max_tokens=500)

    if result["success"]:
        # پیشرفت به مرحله بعد
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
