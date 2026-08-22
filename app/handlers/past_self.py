import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# ============================================================
# سوالات مصاحبه با گذشته
# ============================================================
PAST_QUESTIONS = [
    {"id": "q1", "question": "وقتی به ۵ سال پیش نگاه می‌کنی، چه چیزی در زندگی‌ات بیشتر از همه تغییر کرده؟"},
    {"id": "q2", "question": "بهترین تصمیمی که در زندگی گرفتی چه بود؟ چرا؟"},
    {"id": "q3", "question": "اگر می‌توانستی یک روز از گذشته‌ات را دوباره زندگی کنی، کدام روز بود؟"},
    {"id": "q4", "question": "چیزی که در گذشته آرزو می‌کردی کاش می‌دانستی، امروز چه چیزی است؟"},
    {"id": "q5", "question": "کدام باور یا فکری که قبلاً داشتی، امروز آن را قبول نداری؟"},
    {"id": "q6", "question": "اگر یک پیام به خودت در ۱۰ سال پیش بفرستی، چه می‌گویی؟"},
    {"id": "q7", "question": "چیزی که در گذشته از آن می‌ترسیدی، امروز چطور به آن نگاه می‌کنی؟"},
    {"id": "q8", "question": "بهترین درسی که از یک شکست یا ناامیدی گرفتی چه بود؟"},
    {"id": "q9", "question": "اگر گذشته‌ات یک کتاب بود، عنوانش چه بود؟"},
    {"id": "q10", "question": "چه چیزی را در گذشته رها کردی که امروز به آن افتخار می‌کنی؟"}
]

# ============================================================
# ۱. شروع بخش آیینه‌ی گذشته
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
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except OperationalError:
        user = None

    if not user:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text("❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.", reply_markup=InlineKeyboardMarkup(keyboard))
        db.close()
        return

    # تنظیم current_section برای جلوگیری از تداخل با گفتگو
    context.user_data['current_section'] = 'past_self'
    logger.info(f"🕰️ start_past_self: user_id={user_id}, current_section='past_self'")

    try:
        past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else None
    except:
        past_answers = None
    db.close()

    # اگر پاسخ‌های قبلی وجود دارد → وارد حالت گفتگو می‌شویم
    if past_answers and len(past_answers) > 0:
        context.user_data['past_self_mode'] = True
        context.user_data['past_self_free_chat'] = True
        await message.reply_text(
            "🕰️ **آیینه‌ی گذشته**\n\n"
            "شما قبلاً مصاحبه را کامل کرده‌اید.\n"
            "اکنون هر سوالی درباره‌ی گذشته‌تان دارید، بپرسید. من به‌عنوان «خود گذشته» پاسخ می‌دهم.\n\n"
            "🌱 برای پایان، از دکمه‌ی «بازگشت به خانه» استفاده کنید."
        )
        return

    # اگر مصاحبه‌ای کامل نشده → نمایش گزینه‌ها
    keyboard = [
        [InlineKeyboardButton("🔄 شروع مصاحبه", callback_data="past_self_new_interview")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
    ]
    await message.reply_text(
        "🕰️ **آیینه‌ی گذشته**\n\n"
        "برای شروع، ابتدا باید مصاحبه‌ای درباره‌ی گذشته‌تان انجام دهید.\n"
        "این مصاحبه به من کمک می‌کند تا شما را بهتر بشناسم و پاسخ‌های دقیق‌تری بدهم.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================
# ۲. ارسال سوال بعدی مصاحبه
# ============================================================
async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('past_self_step', 0)
    if step >= len(PAST_QUESTIONS):
        await finish_interview(update, context)
        return

    q = PAST_QUESTIONS[step]
    text = (
        f"🕰️ **مصاحبه با گذشته – سوال {step+1} از {len(PAST_QUESTIONS)}**\n\n"
        f"{q['question']}\n\n✍️ پاسخ خود را بنویسید:"
    )
    keyboard = [
        [InlineKeyboardButton("⏹️ پایان مصاحبه", callback_data="past_self_end_interview")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
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
# ۳. دریافت پاسخ کاربر در حین مصاحبه
# ============================================================
async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('past_self_mode'):
        return

    user_message = update.message.text
    step = context.user_data.get('past_self_step', 0)

    if step >= len(PAST_QUESTIONS):
        await finish_interview(update, context)
        return

    answers = context.user_data.get('past_self_answers', [])
    answers.append({
        "question": PAST_QUESTIONS[step]["question"],
        "answer": user_message
    })
    context.user_data['past_self_answers'] = answers

    try:
        await update.message.delete()
    except:
        pass

    context.user_data['past_self_step'] = step + 1
    await send_next_question(update, context)

# ============================================================
# ۴. پایان مصاحبه و ذخیره
# ============================================================
async def finish_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answers = context.user_data.get('past_self_answers', [])

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.personality_profile = answers
            db.commit()
            logger.info(f"✅ پاسخ‌های کاربر {user_id} ذخیره شد (تعداد: {len(answers)})")
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره: {e}")
    finally:
        db.close()

    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0
    context.user_data['current_section'] = None

    # پس از ذخیره، کاربر به حالت گفتگو هدایت می‌شود
    context.user_data['past_self_mode'] = True
    context.user_data['past_self_free_chat'] = True
    context.user_data['current_section'] = 'past_self'

    text = (
        "✅ **مصاحبه کامل شد!**\n\n"
        f"شما به {len(answers)} سوال پاسخ دادید.\n"
        "اکنون می‌توانید هر سوالی درباره‌ی گذشته‌تان بپرسید و پاسخ «خود گذشته» را دریافت کنید.\n\n"
        "🌱 برای پایان، از دکمه‌ی «بازگشت به خانه» استفاده کنید."
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    if update.callback_query:
        query = update.callback_query
        try:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except:
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# ۵. نمایش پاسخ‌های قبلی (اختیاری)
# ============================================================
async def show_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except:
        user = None

    if not user or not user.personality_profile:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await query.edit_message_text("📭 شما هنوز مصاحبه‌ای کامل نکرده‌اید.", reply_markup=InlineKeyboardMarkup(keyboard))
        db.close()
        return

    answers = user.personality_profile
    text = "📋 **پاسخ‌های شما به مصاحبه‌ی گذشته:**\n\n"
    for i, item in enumerate(answers, 1):
        q = item.get("question", "سوال")
        a = item.get("answer", "پاسخ")[:60] + "..." if len(item.get("answer", "")) > 60 else item.get("answer", "پاسخ")
        text += f"{i}. {q}\n   📝 {a}\n\n"
        if len(text) > 3500:
            text += "\n... و بقیه"
            break

    keyboard = [
        [InlineKeyboardButton("🔄 مصاحبه جدید", callback_data="past_self_new_interview")],
        [InlineKeyboardButton("🗑️ پاک کردن پاسخ‌ها", callback_data="past_self_delete_answers")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    db.close()

# ============================================================
# ۶. پاک کردن پاسخ‌ها
# ============================================================
async def delete_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.personality_profile = None
            db.commit()
            logger.info(f"🗑️ پاسخ‌های کاربر {user_id} پاک شد")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
    finally:
        db.close()

    await query.edit_message_text(
        "✅ پاسخ‌ها پاک شد.\n\n"
        "اکنون می‌توانید مصاحبه‌ی جدیدی شروع کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 شروع مصاحبه", callback_data="past_self_new_interview")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
        ])
    )

# ============================================================
# ۷. شروع مصاحبه جدید
# ============================================================
async def new_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.personality_profile = None
            db.commit()
            logger.info(f"🔄 پاسخ‌های کاربر {user_id} برای مصاحبه جدید پاک شد")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
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
# ۸. پایان زودهنگام مصاحبه (بدون ذخیره)
# ============================================================
async def end_interview_early(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0
    context.user_data['current_section'] = None

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text("⏹️ مصاحبه پایان یافت.", reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# ۹. پردازش پیام‌های کاربر در حالت گفتگو با گذشته
# ============================================================
async def chat_with_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"🕰️ chat_with_past_self: user_id={update.effective_user.id}, "
                f"past_self_mode={context.user_data.get('past_self_mode')}, "
                f"past_self_free_chat={context.user_data.get('past_self_free_chat')}")

    if not context.user_data.get('past_self_mode') or not context.user_data.get('past_self_free_chat'):
        return

    user_id = update.effective_user.id
    user_message = update.message.text

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except:
        user = None

    if not user:
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید.")
        return

    past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else []
    mood_history = user.mood_history or []
    recent_moods = [h.get("mood") for h in mood_history[-7:] if h.get("mood")]

    if recent_moods:
        good_ratio = recent_moods.count("good") / len(recent_moods) if recent_moods else 0
        mood_summary = "روزهای خوب" if good_ratio > 0.6 else "روزهای معمولی" if good_ratio > 0.3 else "روزهای سخت"
    else:
        mood_summary = "اطلاعات کافی از احساساتت ندارم"

    past_text = ""
    if past_answers and len(past_answers) > 0:
        for item in past_answers[:5]:
            past_text += f"- {item.get('question', '')}\n  پاسخ: {item.get('answer', '')[:120]}...\n"

    prompt = f"""تو «نسخه‌ی گذشته» {user.preferred_name} هستی، حدود ۳ تا ۵ سال پیش.

⚠️ مهم: تو یک ربات نیستی. تو خودِ {user.preferred_name} هستی در زمان گذشته.

ویژگی‌های تو:
- تو همان شخص هستی، اما در زمان گذشته
- باورها، نگرش‌ها و سبک گفتار تو متعلق به آن زمان است
- پاسخ‌هایت طبیعی، انسانی و صمیمی است
- هرگز پاسخ‌های رباتیک یا کلیشه‌ای نمی‌دهی
- لحن تو همیشه صمیمی، گرم و طبیعی است (نه طنز، نه رسمی)

اطلاعات کاربر در زمان حال:
- نام: {user.preferred_name}
- سن فعلی: {user.age}
- جنسیت: {'مرد' if user.gender == 'male' else 'زن'}
- احساسات اخیر: {mood_summary}

پاسخ‌هایی که کاربر قبلاً به سوالات گذشته داده:
{past_text if past_text else "هنوز مصاحبه‌ای کامل نشده."}

حالا کاربر (خودت در زمان حال) با تو (خودت در گذشته) گفتگو می‌کند.
پیام او: {user_message}

پاسخ خود را به‌عنوان «خود گذشته» بنویس (با لحن صمیمی و طبیعی):"""

    db.close()

    result = call_openrouter(prompt, temperature=0.85, max_tokens=500, section="past_self")

    if result["success"]:
        await update.message.reply_text(f"🕰️ **خود گذشته:**\n\n{result['reply']}")
    else:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await update.message.reply_text(
            f"🕰️ **خود گذشته:**\n\nمتأسفم، الان نمی‌تونم خوب فکر کنم.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
