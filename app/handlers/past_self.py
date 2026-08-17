import logging
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

# سوالات عمیق و علمی برای مصاحبه با گذشته
PAST_QUESTIONS = [
    {
        "id": "q1",
        "question": "وقتی به ۵ سال پیش نگاه می‌کنی، چه چیزی در زندگی‌ات بیشتر از همه تغییر کرده؟"
    },
    {
        "id": "q2",
        "question": "بهترین تصمیمی که در زندگی گرفتی چه بود؟ چرا؟"
    },
    {
        "id": "q3",
        "question": "اگر می‌توانستی یک روز از گذشته‌ات را دوباره زندگی کنی، کدام روز بود؟"
    },
    {
        "id": "q4",
        "question": "چیزی که در گذشته آرزو می‌کردی کاش می‌دانستی، امروز چه چیزی است؟"
    },
    {
        "id": "q5",
        "question": "کدام باور یا فکری که قبلاً داشتی، امروز آن را قبول نداری؟"
    },
    {
        "id": "q6",
        "question": "اگر یک پیام به خودت در ۱۰ سال پیش بفرستی، چه می‌گویی؟"
    },
    {
        "id": "q7",
        "question": "چیزی که در گذشته از آن می‌ترسیدی، امروز چطور به آن نگاه می‌کنی؟"
    },
    {
        "id": "q8",
        "question": "بهترین درسی که از یک شکست یا ناامیدی گرفتی چه بود؟"
    },
    {
        "id": "q9",
        "question": "اگر گذشته‌ات یک کتاب بود، عنوانش چه بود؟"
    },
    {
        "id": "q10",
        "question": "چه چیزی را در گذشته رها کردی که امروز به آن افتخار می‌کنی؟"
    }
]

# ============================================================
# ۱. شروع بخش خود گذشته
# ============================================================
async def start_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await message.reply_text("❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        return

    # بررسی آیا کاربر قبلاً مصاحبه را شروع کرده
    past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else None

    if past_answers:
        # کاربر قبلاً پاسخ داده است
        keyboard = [
            [InlineKeyboardButton("📋 دیدن پاسخ‌های قبلی", callback_data="past_self_show_answers")],
            [InlineKeyboardButton("🔄 مصاحبه‌ی جدید (پاسخ‌های قبلی پاک می‌شود)", callback_data="past_self_new_interview")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ]
        await message.reply_text(
            "🕰️ **خود گذشته**\n\n"
            "شما قبلاً در مصاحبه‌ی «خود گذشته» شرکت کرده‌اید.\n"
            "می‌توانید پاسخ‌های قبلی را ببینید یا مصاحبه‌ای جدید شروع کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    else:
        # شروع مصاحبه
        context.user_data['past_self_step'] = 0
        context.user_data['past_self_answers'] = []
        await send_next_question(update, context)

# ============================================================
# ۲. ارسال سوال بعدی
# ============================================================
async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('past_self_step', 0)

    if step >= len(PAST_QUESTIONS):
        await finish_interview(update, context)
        return

    question_data = PAST_QUESTIONS[step]
    text = (
        f"🕰️ **مصاحبه با گذشته – سوال {step+1} از {len(PAST_QUESTIONS)}**\n\n"
        f"{question_data['question']}\n\n"
        f"✍️ پاسخ خود را به‌صورت کامل بنویسید. (هر چقدر دقیق‌تر، بهتر)"
    )

    keyboard = [[InlineKeyboardButton("⏹️ پایان مصاحبه", callback_data="past_self_end_interview")]]

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# ۳. دریافت پاسخ کاربر
# ============================================================
async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if not context.user_data.get('past_self_mode'):
        return

    step = context.user_data.get('past_self_step', 0)

    # ذخیره پاسخ
    answers = context.user_data.get('past_self_answers', [])
    answers.append({
        "question": PAST_QUESTIONS[step]["question"],
        "answer": user_message,
        "question_id": PAST_QUESTIONS[step]["id"]
    })
    context.user_data['past_self_answers'] = answers

    # رفتن به سوال بعدی
    context.user_data['past_self_step'] = step + 1

    # حذف پیام کاربر (برای تمیزی)
    try:
        await update.message.delete()
    except:
        pass

    await send_next_question(update, context)

# ============================================================
# ۴. پایان مصاحبه و ذخیره
# ============================================================
async def finish_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answers = context.user_data.get('past_self_answers', [])

    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    if user:
        user.personality_profile = answers  # ذخیره پاسخ‌ها
        db.commit()
    db.close()

    context.user_data['past_self_mode'] = False

    # نمایش خلاصه
    text = (
        "✅ **مصاحبه با گذشته کامل شد!**\n\n"
        f"شما به {len(answers)} سوال درباره‌ی گذشته‌تان پاسخ دادید.\n\n"
        "این پاسخ‌ها ذخیره شده‌اند. هر وقت خواستید، می‌توانید:\n"
        "• پاسخ‌های خود را مرور کنید\n"
        "• مصاحبه‌ی جدیدی شروع کنید\n"
        "• بر اساس پاسخ‌ها، با هوش مصنوعی درباره‌ی گذشته‌تان گفتگو کنید\n\n"
        "از منو، گزینه‌ی «خود گذشته» را انتخاب کنید."
    )

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]

    if update.callback_query:
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# ۵. نمایش پاسخ‌های قبلی
# ============================================================
async def show_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()

    if not user or not user.personality_profile:
        await query.edit_message_text("📭 شما هنوز مصاحبه‌ای کامل نکرده‌اید.")
        return

    answers = user.personality_profile
    text = "📋 **پاسخ‌های شما به مصاحبه‌ی گذشته:**\n\n"

    for i, item in enumerate(answers, 1):
        q = item.get("question", "سوال")
        a = item.get("answer", "پاسخ")
        # فقط ۳۰ کاراکتر اول برای خلاصه
        a_short = a[:50] + "..." if len(a) > 50 else a
        text += f"{i}. {q}\n   📝 {a_short}\n\n"

        if len(text) > 3500:
            text += "\n... و سوالات بیشتر"
            break

    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data="past_self_menu")],
        [InlineKeyboardButton("🗑️ پاک کردن پاسخ‌ها", callback_data="past_self_delete_answers")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# ۶. پاک کردن پاسخ‌ها
# ============================================================
async def delete_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    if user:
        user.personality_profile = None
        db.commit()
    db.close()

    await query.edit_message_text(
        "✅ پاسخ‌های شما پاک شد.\n\n"
        "اکنون می‌توانید مصاحبه‌ی جدیدی را شروع کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 شروع مصاحبه‌ی جدید", callback_data="past_self_new_interview")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ])
    )

# ============================================================
# ۷. شروع مصاحبه‌ی جدید
# ============================================================
async def new_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # پاک کردن پاسخ‌های قبلی از دیتابیس
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    if user:
        user.personality_profile = None
        db.commit()
    db.close()

    context.user_data['past_self_mode'] = True
    context.user_data['past_self_step'] = 0
    context.user_data['past_self_answers'] = []

    try:
        await query.message.delete()
    except:
        pass

    await send_next_question(update, context)

# ============================================================
# ۸. پایان زودهنگام مصاحبه
# ============================================================
async def end_interview_early(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['past_self_mode'] = False

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
    await query.message.reply_text(
        "⏹️ **مصاحبه به پایان رسید.**\n\n"
        "پاسخ‌هایی که تا الان داده‌اید ذخیره نشده‌اند.\n"
        "اگر می‌خواهید از اول شروع کنید، گزینه‌ی «مصاحبه‌ی جدید» را انتخاب کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================
# ۹. گفتگوی آزاد با گذشته (با کمک هوش مصنوعی و پاسخ‌های کاربر)
# ============================================================
async def chat_with_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # دریافت پاسخ‌های قبلی کاربر
    past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else []

    # دریافت احساسات اخیر
    mood_history = user.mood_history or []
    recent_moods = [h.get("mood") for h in mood_history[-7:] if h.get("mood")]

    if recent_moods:
        good_ratio = recent_moods.count("good") / len(recent_moods) if recent_moods else 0
        mood_summary = "روزهای خوبی داشته‌ای" if good_ratio > 0.6 else "روزهای معمولی و متغیر" if good_ratio > 0.3 else "چند روز سخت را گذرانده‌ای"
    else:
        mood_summary = "اطلاعات کافی از احساساتت ندارم"

    # ساخت پرامپت برای OpenRouter
    past_answers_text = ""
    if past_answers:
        for item in past_answers[:5]:  # فقط ۵ پاسخ اخیر برای جلوگیری از طولانی شدن
            past_answers_text += f"- {item.get('question', '')}\n  پاسخ: {item.get('answer', '')[:100]}...\n"

    prompt = f"""تو یک هم‌نشین صمیمی و باهوش هستی که با کاربری درباره‌ی گذشته‌اش گفتگو می‌کند.

اطلاعات کاربر:
- نام: {user.preferred_name}
- سن: {user.age}
- احساسات اخیر: {mood_summary}

پاسخ‌های قبلی کاربر به سوالات «خود گذشته»:
{past_answers_text if past_answers_text else "کاربر هنوز مصاحبه‌ای کامل نکرده است."}

کاربر حالا در گفتگویی آزاد درباره‌ی گذشته‌اش سوال می‌پرسد یا نظری می‌دهد.

وظیفه‌ات:
۱. با همدلی، گرمی و احترام پاسخ بده.
۲. از پاسخ‌های قبلی کاربر برای شخصی‌سازی پاسخ استفاده کن.
۳. اگر کاربر درباره‌ی گذشته‌اش سوالی دارد، با دقت و دانش پاسخ بده.
۴. حس کن که یک دوست قدیمی هستی که کاربر را خوب می‌شناسد.

پیام کاربر: {user_message}

پاسخ خود را به‌عنوان یک همراه صمیمی بنویس:
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
            "temperature": 0.85,
            "max_tokens": 400
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json()

        if response.status_code == 200:
            reply = response_data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                await update.message.reply_text(f"🕰️ **همراه گذشته:**\n\n{reply}")
                return
    except Exception as e:
        logger.error(f"خطا در گفتگوی گذشته: {e}")

    await update.message.reply_text(
        "🕰️ **همراه گذشته:**\n\n"
        "متأسفم، الان نمی‌تونم خوب فکر کنم. شاید بعداً بهتر بتونم کمک کنم."
        )
