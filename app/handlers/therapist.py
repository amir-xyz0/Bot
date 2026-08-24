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
    logger.info("🔥 start_therapy فراخوانی شد!")
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

    if not message:
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except Exception as e:
        logger.error(f"❌ خطا در دیتابیس: {e}")
        await message.reply_text("❌ خطا در ارتباط با دیتابیس.")
        db.close()
        return
    db.close()

    if not user:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(
            "❗ ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    context.user_data['current_section'] = 'therapist'
    context.user_data['therapy_mode'] = True
    context.user_data['therapy_step'] = 'start'

    logger.info(f"🧠 start_therapy: user_id={user_id}")

    keyboard = [[InlineKeyboardButton("🔚 پایان جلسه", callback_data="end_therapy")]]
    await message.reply_text(
        f"🧠 **مشاوره درون**\n\n{THERAPY_QUESTIONS['start']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def chat_with_therapist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔥 chat_with_therapist فراخوانی شد!")
    
    if not update.message or not update.message.text:
        logger.info("⏭️ پیام متنی نیست")
        return
    if update.message.text.startswith('/'):
        logger.info("⏭️ پیام کامند است")
        return
    
    if context.user_data.get('current_section') != 'therapist':
        logger.info(f"⏭️ عبور از therapist (current_section={context.user_data.get('current_section')})")
        return

    if not context.user_data.get('therapy_mode'):
        logger.info("⏭️ therapy_mode=False")
        return

    user_id = update.effective_user.id
    user_message = update.message.text
    logger.info(f"🧠 chat_with_therapist: user_id={user_id}")

    # ارسال پیام "در حال پردازش..."
    loading_msg = await update.message.reply_text("⏳ در حال پردازش...")

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except Exception as e:
        logger.error(f"❌ خطا در دیتابیس: {e}")
        await loading_msg.delete()
        await update.message.reply_text("❌ خطا در ارتباط با دیتابیس.")
        db.close()
        return
    db.close()

    if not user:
        logger.warning(f"⚠️ کاربر {user_id} ثبت‌نام نکرده")
        await loading_msg.delete()
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید. /start را بزنید.")
        return

    step = context.user_data.get('therapy_step', 'start')

    # ============================================================
    # پرامپت فوق‌العاده صمیمی، گرم و حرفه‌ای - بدون "سلام" تکراری
    # ============================================================
    prompt = f"""تو یک همراه و مشاور گرم، صمیمی و فوق‌العاده حرفه‌ای هستی. 
دلت می‌خواهد کاربر احساس کند با یک دوست قدیمی و دانا حرف می‌زند.

شخصیت تو:
- لحنت گرم، انسانی، پر از همدلی و درک عمیق است
- مانند یک حکیم مهربان و یک دوست صمیمی صحبت می‌کنی
- از جملات تأمل‌برانگیز و پرسش‌های سقراطی استفاده می‌کنی
- هرگز قضاوت نمی‌کنی، فقط همراهی و راهنمایی می‌کنی
- پاسخ‌هایت سرشار از انرژی مثبت، امید و آرامش است
- احساسات کاربر را درک می‌کنی و به آن احترام می‌گذاری
- از کلمات ساده، دلنشین و روان استفاده می‌کنی
- پاسخ‌هایت مختصر، مفید و تأثیرگذار است (حداکثر ۳-۴ پاراگراف)

مرحله فعلی: {step}
سوال استاندارد این مرحله: {THERAPY_QUESTIONS.get(step, '')}

اطلاعات کاربر:
- نام: {user.preferred_name}
- سن: {user.age}

پیام کاربر: {user_message}

وظیفه‌ات:
۱. با همدلی و گرمی پاسخ بده.
۲. پاسخ باید حس کند که یک انسان واقعی با او حرف می‌زند.
۳. در پایان، سوال بعدی را به‌صورت طبیعی بپرس (مثل یک مکالمه واقعی).
۴. از جملات الهام‌بخش و امیدوارکننده استفاده کن.

⭐ پاسخ خود را بدون هیچ مقدمه‌ای و مستقیم شروع کن.
⭐ هیچوقت با «سلام» یا «درود» شروع نکن.
⭐ فقط پاسخ بده، طوری که انگار وسط یک مکالمه صمیمی هستی."""

    result = call_openrouter(prompt, temperature=0.8, max_tokens=500, section="therapist")

    # حذف پیام "در حال پردازش..."
    try:
        await loading_msg.delete()
    except:
        pass

    if result["success"]:
        steps = ['start', 'identify', 'challenge', 'reframe', 'action']
        current_idx = steps.index(step) if step in steps else 0
        if current_idx < len(steps) - 1:
            context.user_data['therapy_step'] = steps[current_idx + 1]

        # فقط پاسخ بدون هدر و بدون دکمه
        await update.message.reply_text(result["reply"])
    else:
        logger.error(f"❌ خطا در پاسخ به کاربر {user_id}: {result['error']}")
        await update.message.reply_text(
            f"متأسفم، الان نمی‌تونم خوب فکر کنم. لطفاً دوباره تلاش کن. ❤️"
        )

async def end_therapy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['current_section'] = None
    context.user_data['therapy_mode'] = False
    context.user_data['therapy_step'] = 'start'

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text(
        "🌿 **جلسه‌ی مشاوره به پایان رسید.**\n\n"
        "هر زمان که نیاز داشتی، من اینجام تا همراهت باشم. 🌸",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
