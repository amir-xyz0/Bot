import logging
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# ============================================================
# سوالات عمیق و علمی برای مصاحبه با گذشته
# ============================================================
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
    """ورود به بخش خود گذشته - نمایش گزینه‌ها"""
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
    except OperationalError:
        user = None

    if not user:
        await message.reply_text("❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        db.close()
        return

    # بررسی وجود پاسخ‌های قبلی
    try:
        past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else None
    except:
        past_answers = None

    if past_answers and len(past_answers) > 0:
        keyboard = [
            [InlineKeyboardButton("📋 دیدن پاسخ‌های قبلی", callback_data="past_self_show_answers")],
            [InlineKeyboardButton("🔄 مصاحبه‌ی جدید (پاسخ‌ها پاک می‌شود)", callback_data="past_self_new_interview")],
            [InlineKeyboardButton("💬 گفتگوی آزاد با گذشته", callback_data="past_self_free_chat")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        await message.reply_text(
            "🕰️ **خود گذشته**\n\n"
            "شما قبلاً در مصاحبه‌ی «خود گذشته» شرکت کرده‌اید.\n\n"
            "• می‌توانید پاسخ‌های قبلی را مرور کنید.\n"
            "• مصاحبه‌ی جدیدی شروع کنید.\n"
            "• یا با هوش مصنوعی درباره‌ی گذشته‌تان گفتگو کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        db.close()
        return

    # شروع مصاحبه جدید
    context.user_data['past_self_step'] = 0
    context.user_data['past_self_answers'] = []
    context.user_data['past_self_mode'] = True
    db.close()
    await send_next_question(update, context)

# ============================================================
# ۲. ارسال سوال بعدی
# ============================================================
async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال سوال بعدی مصاحبه"""
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
        try:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except:
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# ۳. دریافت پاسخ کاربر
# ============================================================
async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت و ذخیره پاسخ کاربر به سوال فعلی"""
    user_id = update.effective_user.id
    user_message = update.message.text

    if not context.user_data.get('past_self_mode'):
        return

    step = context.user_data.get('past_self_step', 0)

    if step >= len(PAST_QUESTIONS):
        await finish_interview(update, context)
        return

    # ذخیره پاسخ
    answers = context.user_data.get('past_self_answers', [])
    answers.append({
        "question": PAST_QUESTIONS[step]["question"],
        "answer": user_message,
        "question_id": PAST_QUESTIONS[step]["id"]
    })
    context.user_data['past_self_answers'] = answers

    # حذف پیام کاربر
    try:
        await update.message.delete()
    except:
        pass

    # رفتن به سوال بعدی
    context.user_data['past_self_step'] = step + 1
    await send_next_question(update, context)

# ============================================================
# ۴. پایان مصاحبه و ذخیره در دیتابیس
# ============================================================
async def finish_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پایان مصاحبه و ذخیره پاسخ‌ها در دیتابیس"""
    user_id = update.effective_user.id
    answers = context.user_data.get('past_self_answers', [])

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.personality_profile = answers
            db.commit()
    except Exception as e:
        logger.error(f"خطا در ذخیره پاسخ‌ها: {e}")
    finally:
        db.close()

    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0

    text = (
        "✅ **مصاحبه با گذشته کامل شد!**\n\n"
        f"شما به {len(answers)} سوال درباره‌ی گذشته‌تان پاسخ دادید.\n\n"
        "حالا می‌توانید:\n"
        "• پاسخ‌های خود را مرور کنید\n"
        "• مصاحبه‌ی جدیدی شروع کنید\n"
        "• با هوش مصنوعی درباره‌ی گذشته‌تان گفتگو کنید"
    )

    keyboard = [
        [InlineKeyboardButton("📋 دیدن پاسخ‌ها", callback_data="past_self_show_answers")],
        [InlineKeyboardButton("💬 گفتگوی آزاد با گذشته", callback_data="past_self_free_chat")],
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
    ]

    if update.callback_query:
        query = update.callback_query
        try:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except:
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# ۵. نمایش پاسخ‌های قبلی
# ============================================================
async def show_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پاسخ‌های ذخیره‌شده کاربر"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except:
        user = None

    if not user or not user.personality_profile:
        await query.edit_message_text("📭 شما هنوز مصاحبه‌ای کامل نکرده‌اید.")
        db.close()
        return

    answers = user.personality_profile
    text = "📋 **پاسخ‌های شما به مصاحبه‌ی گذشته:**\n\n"

    for i, item in enumerate(answers, 1):
        q = item.get("question", "سوال")
        a = item.get("answer", "پاسخ")
        a_short = a[:60] + "..." if len(a) > 60 else a
        text += f"{i}. {q}\n   📝 {a_short}\n\n"
        if len(text) > 3500:
            text += "\n... و سوالات بیشتر"
            break

    keyboard = [
        [InlineKeyboardButton("💬 گفتگوی آزاد", callback_data="past_self_free_chat")],
        [InlineKeyboardButton("🔄 مصاحبه‌ی جدید", callback_data="past_self_new_interview")],
        [InlineKeyboardButton("🗑️ پاک کردن پاسخ‌ها", callback_data="past_self_delete_answers")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="past_self_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    db.close()

# ============================================================
# ۶. پاک کردن پاسخ‌ها
# ============================================================
async def delete_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاک کردن تمام پاسخ‌های ذخیره‌شده"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.personality_profile = None
            db.commit()
    except Exception as e:
        logger.error(f"خطا در پاک کردن پاسخ‌ها: {e}")
    finally:
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
    """شروع مصاحبه‌ی جدید (پاک کردن پاسخ‌های قبلی)"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # پاک کردن پاسخ‌های قبلی از دیتابیس
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.personality_profile = None
            db.commit()
    except Exception as e:
        logger.error(f"خطا در پاک کردن پاسخ‌ها: {e}")
    finally:
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
    """پایان زودهنگام مصاحبه بدون ذخیره"""
    query = update.callback_query
    await query.answer()
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
    await query.message.reply_text(
        "⏹️ **مصاحبه به پایان رسید.**\n\n"
        "پاسخ‌هایی که تا الان داده‌اید ذخیره نشده‌اند.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================
# ۹. گفتگوی آزاد با گذشته (با کمک هوش مصنوعی)
# ============================================================
async def free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به حالت گفتگوی آزاد با هوش مصنوعی"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except:
        user = None

    if not user:
        await query.edit_message_text("❗ شما ثبت‌نام نکرده‌اید.")
        db.close()
        return

    context.user_data['past_self_mode'] = True
    context.user_data['past_self_free_chat'] = True

    past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else []

    try:
        await query.message.delete()
    except:
        pass

    if past_answers and len(past_answers) > 0:
        text = (
            "💬 **گفتگوی آزاد با گذشته**\n\n"
            "من پاسخ‌های قبلی شما را مطالعه کرده‌ام.\n"
            "حالا می‌توانید درباره‌ی هر موضوعی از گذشته‌تان سوال بپرسید.\n\n"
            "مثلاً:\n"
            "• «چرا فلان تصمیم رو گرفتم؟»\n"
            "• «اگر می‌توانستم به خودم در ۲۰ سالگی چه بگویم؟»\n"
            "• «چطور می‌توانم از اشتباهات گذشته‌ام یاد بگیرم؟»\n\n"
            "برای پایان گفتگو، دکمه‌ی زیر را بزنید."
        )
    else:
        text = (
            "💬 **گفتگوی آزاد با گذشته**\n\n"
            "شما هنوز مصاحبه‌ای کامل نکرده‌اید.\n"
            "اما می‌توانید درباره‌ی هر موضوعی از گذشته‌تان سوال بپرسید.\n\n"
            "برای پایان گفتگو، دکمه‌ی زیر را بزنید."
        )

    keyboard = [[InlineKeyboardButton("🔚 پایان گفتگو", callback_data="past_self_end_free_chat")]]
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    db.close()

# ============================================================
# ۱۰. پایان گفتگوی آزاد
# ============================================================
async def end_free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پایان گفتگوی آزاد با گذشته"""
    query = update.callback_query
    await query.answer()
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_free_chat'] = False

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
    await query.message.reply_text(
        "✅ **گفتگوی آزاد به پایان رسید.**\n\n"
        "هر وقت خواستید دوباره گفتگو کنید، از منو انتخاب کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================
# ۱۱. پردازش پیام‌های کاربر در حالت گفتگوی آزاد
# ============================================================
async def chat_with_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مکالمه در حالت گفتگوی آزاد با هوش مصنوعی"""
    user_id = update.effective_user.id
    user_message = update.message.text

    if not context.user_data.get('past_self_mode') or not context.user_data.get('past_self_free_chat'):
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except:
        user = None

    if not user:
        await update.message.reply_text("❗ شما ثبت‌نام نکرده‌اید.")
        db.close()
        return

    past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else []

    # تحلیل احساسات اخیر
    mood_history = user.mood_history or []
    recent_moods = [h.get("mood") for h in mood_history[-7:] if h.get("mood")]
    if recent_moods:
        good_ratio = recent_moods.count("good") / len(recent_moods) if recent_moods else 0
        if good_ratio > 0.6:
            mood_summary = "روزهای خوبی داشته‌ای"
        elif good_ratio > 0.3:
            mood_summary = "روزهای معمولی و متغیر داشته‌ای"
        else:
            mood_summary = "چند روز سخت را گذرانده‌ای"
    else:
        mood_summary = "اطلاعات کافی از احساساتت ندارم"

    # ساخت پرامپت
    past_answers_text = ""
    if past_answers and len(past_answers) > 0:
        for item in past_answers[:5]:
            past_answers_text += f"- {item.get('question', '')}\n  پاسخ: {item.get('answer', '')[:100]}...\n"

    prompt = f"""تو یک همراه صمیمی و باهوش هستی که با کاربری درباره‌ی گذشته‌اش گفتگو می‌کند.

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

پاسخ خود را به‌عنوان یک همراه صمیمی بنویس (بدون توضیحات اضافی):
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
            "max_tokens": 450
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json()

        if response.status_code == 200:
            reply = response_data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                await update.message.reply_text(f"🕰️ **همراه گذشته:**\n\n{reply}")
                db.close()
                return
    except Exception as e:
        logger.error(f"خطا در گفتگوی گذشته: {e}")

    await update.message.reply_text(
        "🕰️ **همراه گذشته:**\n\n"
        "متأسفم، الان نمی‌تونم خوب فکر کنم. شاید بعداً بهتر بتونم کمک کنم."
    )
    db.close()
