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
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(
            "❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        db.close()
        return

    # 🔥 تنظیم current_section برای جلوگیری از تداخل با گفتگوی عمومی
    context.user_data['current_section'] = 'past_self'
    logger.info(f"🕰️ start_past_self: user_id={user_id}, current_section=past_self")

    # بررسی وجود پاسخ‌های قبلی
    try:
        past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else None
    except:
        past_answers = None
    db.close()

    if past_answers and len(past_answers) > 0:
        keyboard = [
            [InlineKeyboardButton("📋 دیدن پاسخ‌های قبلی", callback_data="past_self_show_answers")],
            [InlineKeyboardButton("🔄 مصاحبه‌ی جدید", callback_data="past_self_new_interview")],
            [InlineKeyboardButton("💬 گفتگوی آزاد با گذشته", callback_data="past_self_free_chat")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
        ]
        await message.reply_text(
            "🕰️ **آیینه‌ی گذشته**\n\n"
            "شما قبلاً در مصاحبه‌ای شرکت کرده‌اید که به من کمک کرد تا شما را بهتر بشناسم.\n\n"
            "• می‌توانید پاسخ‌های قبلی را مرور کنید.\n"
            "• مصاحبه‌ی جدیدی شروع کنید.\n"
            "• یا با نسخه‌ی گذشته‌ی خود گفتگو کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # شروع مصاحبه جدید
    context.user_data['past_self_mode'] = True
    context.user_data['past_self_step'] = 0
    context.user_data['past_self_answers'] = []
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
        f"✍️ پاسخ خود را به‌صورت کامل بنویسید. هر چقدر دقیق‌تر، بهتر می‌توانم شما را بشناسم."
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
# ۳. دریافت پاسخ کاربر (فقط در حالت مصاحبه)
# ============================================================
async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت پاسخ کاربر – فقط در حالت مصاحبه (نه گفتگوی آزاد)"""
    # فقط اگر کاربر در بخش خودگذشته باشد
    #if context.user_data.get('current_section') != 'past_self':
        #return
    
    if not context.user_data.get('past_self_mode'):
        return
    
    # اگر گفتگوی آزاد فعاله، کاری نکن تا هندلر بعدی اجرا بشه
    if context.user_data.get('past_self_free_chat'):
        return

    user_message = update.message.text
    step = context.user_data.get('past_self_step', 0)
    user_id = update.effective_user.id
    logger.info(f"📩 receive_answer: user_id={user_id}, step={step}")

    if step >= len(PAST_QUESTIONS):
        await finish_interview(update, context)
        return

    answers = context.user_data.get('past_self_answers', [])
    answers.append({
        "question": PAST_QUESTIONS[step]["question"],
        "answer": user_message
    })
    context.user_data['past_self_answers'] = answers

    # حذف پیام کاربر برای تمیزی
    try:
        await update.message.delete()
    except:
        pass

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
            logger.info(f"✅ پاسخ‌های کاربر {user_id} ذخیره شد (تعداد: {len(answers)})")
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره پاسخ‌ها: {e}")
    finally:
        db.close()

    # 🔥 پاک کردن current_section هنگام خروج از مصاحبه
    context.user_data['current_section'] = None
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0

    logger.info(f"🕰️ finish_interview: current_section پاک شد")

    text = (
        "✅ **مصاحبه با گذشته کامل شد!**\n\n"
        f"شما به {len(answers)} سوال درباره‌ی گذشته‌تان پاسخ دادید.\n\n"
        "حالا می‌توانید:\n"
        "• پاسخ‌های خود را مرور کنید\n"
        "• مصاحبه‌ی جدیدی شروع کنید\n"
        "• با نسخه‌ی گذشته‌ی خود گفتگو کنید"
    )

    keyboard = [
        [InlineKeyboardButton("📋 دیدن پاسخ‌ها", callback_data="past_self_show_answers")],
        [InlineKeyboardButton("💬 گفتگوی آزاد با گذشته", callback_data="past_self_free_chat")],
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
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await query.edit_message_text(
            "📭 شما هنوز مصاحبه‌ای کامل نکرده‌اید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
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
        [InlineKeyboardButton("🔄 مصاحبه‌ی جدید", callback_data="past_self_new_interview")],
        [InlineKeyboardButton("🗑️ پاک کردن پاسخ‌ها", callback_data="past_self_delete_answers")],
        [InlineKeyboardButton("💬 گفتگوی آزاد با گذشته", callback_data="past_self_free_chat")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
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
            logger.info(f"🗑️ پاسخ‌های کاربر {user_id} پاک شد")
    except Exception as e:
        logger.error(f"❌ خطا در پاک کردن پاسخ‌ها: {e}")
    finally:
        db.close()

    await query.edit_message_text(
        "✅ پاسخ‌های شما پاک شد.\n\n"
        "اکنون می‌توانید مصاحبه‌ی جدیدی را شروع کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 شروع مصاحبه‌ی جدید", callback_data="past_self_new_interview")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
        ])
    )

# ============================================================
# ۷. شروع مصاحبه‌ی جدید (پاک کردن پاسخ‌های قبلی)
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
            logger.info(f"🔄 پاسخ‌های کاربر {user_id} برای مصاحبه جدید پاک شد")
    except Exception as e:
        logger.error(f"❌ خطا در پاک کردن پاسخ‌ها: {e}")
    finally:
        db.close()

    # 🔥 تنظیم current_section برای ورود به مصاحبه جدید
    context.user_data['current_section'] = 'past_self'
    context.user_data['past_self_mode'] = True
    context.user_data['past_self_step'] = 0
    context.user_data['past_self_answers'] = []
    context.user_data['past_self_free_chat'] = False

    logger.info(f"🕰️ new_interview: user_id={user_id}, current_section=past_self")

    try:
        await query.message.delete()
    except:
        pass

    await send_next_question(update, context)

# ============================================================
# ۸. پایان زودهنگام مصاحبه (بدون ذخیره)
# ============================================================
async def end_interview_early(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پایان زودهنگام مصاحبه بدون ذخیره"""
    query = update.callback_query
    await query.answer()
    
    # 🔥 پاک کردن current_section
    context.user_data['current_section'] = None
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0

    logger.info(f"🕰️ end_interview_early: current_section پاک شد")

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text(
        "⏹️ **مصاحبه به پایان رسید.**\n\n"
        "پاسخ‌هایی که تا الان داده‌اید ذخیره نشده‌اند.\n"
        "اگر می‌خواهید از اول شروع کنید، گزینه‌ی «مصاحبه‌ی جدید» را انتخاب کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================
# ۹. ورود به گفتگوی آزاد با گذشته (با هوش مصنوعی)
# ============================================================
async def free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ورود به حالت گفتگوی آزاد با نسخه‌ی گذشته خود"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except:
        user = None

    if not user:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await query.edit_message_text(
            "❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        db.close()
        return

    # 🔥 تنظیم current_section برای گفتگوی آزاد
    context.user_data['current_section'] = 'past_self'
    context.user_data['past_self_mode'] = True
    context.user_data['past_self_free_chat'] = True

    logger.info(f"💬 free_chat: user_id={user_id}, current_section=past_self, past_self_free_chat=True")

    past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else []
    db.close()

    try:
        await query.message.delete()
    except:
        pass

    if past_answers and len(past_answers) > 0:
        text = (
            "🕰️ **گفتگوی آزاد با گذشته**\n\n"
            "من پاسخ‌های قبلی شما را مطالعه کرده‌ام و نسخه‌ای از شما در گذشته را درک کرده‌ام.\n"
            "حالا می‌توانید با آن نسخه گفتگو کنید.\n\n"
            "مثلاً بپرسید:\n"
            "• «چرا فلان تصمیم رو گرفتی؟»\n"
            "• «اگر می‌توانستی به خودت در ۲۰ سالگی چه بگویی؟»\n"
            "• «چطور می‌توانم از اشتباهاتت یاد بگیرم؟»\n\n"
            "🌱 **با خودت در گذشته حرف بزن...**"
        )
    else:
        text = (
            "🕰️ **گفتگوی آزاد با گذشته**\n\n"
            "شما هنوز مصاحبه‌ای کامل نکرده‌اید، اما باز هم می‌توانید با نسخه‌ی گذشته‌تان گفتگو کنید.\n"
            "هر سوالی درباره‌ی گذشته‌ات داری، بپرس.\n\n"
            "🌱 **با خودت در گذشته حرف بزن...**"
        )

    keyboard = [
        [InlineKeyboardButton("🔚 پایان گفتگو", callback_data="past_self_end_free_chat")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
    ]
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# ۱۰. پایان گفتگوی آزاد
# ============================================================
async def end_free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پایان گفتگوی آزاد با گذشته"""
    query = update.callback_query
    await query.answer()
    
    # 🔥 پاک کردن current_section
    context.user_data['current_section'] = None
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_free_chat'] = False

    logger.info(f"💬 end_free_chat: current_section پاک شد")

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text(
        "✅ **گفتگوی آزاد به پایان رسید.**\n\n"
        "هر وقت خواستید دوباره با خودتان در گذشته گفتگو کنید، از منو انتخاب کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============================================================
# ۱۱. پردازش گفتگوی آزاد با گذشته (پرامپت اختصاصی و مستقل)
# ============================================================
async def chat_with_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مکالمه با نسخه‌ی گذشته خود (کاملاً مستقل از chat_style)"""
    # فقط اگر کاربر در بخش خودگذشته باشد
    #if context.user_data.get('current_section') != 'past_self':
        #logger.info(f"⏭️ chat_with_past_self: عبور (current_section={context.user_data.get('current_section')})")
        #return

    if not context.user_data.get('past_self_mode') or not context.user_data.get('past_self_free_chat'):
        return

    user_id = update.effective_user.id
    user_message = update.message.text
    logger.info(f"💬 chat_with_past_self: user_id={user_id}, message={user_message[:30]}...")

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except:
        user = None

    if not user:
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید.")
        return

    # دریافت اطلاعات کاربر
    past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else []
    mood_history = user.mood_history or []
    recent_moods = [h.get("mood") for h in mood_history[-7:] if h.get("mood")]

    # تحلیل احساسات اخیر
    if recent_moods:
        good_ratio = recent_moods.count("good") / len(recent_moods) if recent_moods else 0
        if good_ratio > 0.6:
            mood_summary = "این روزها روحیه‌ات خوب بوده"
        elif good_ratio > 0.3:
            mood_summary = "این روزها حال و هوای معمولی داری"
        else:
            mood_summary = "این روزها کمی سختی می‌گذرانی"
    else:
        mood_summary = "هنوز اطلاعات کافی از احساساتت ندارم"

    # ساخت متن پاسخ‌های قبلی
    past_text = ""
    if past_answers and len(past_answers) > 0:
        for item in past_answers[:5]:
            past_text += f"- {item.get('question', '')}\n  پاسخ: {item.get('answer', '')[:120]}...\n"

    # ============================================================
    # پرامپت اختصاصی خود گذشته – کاملاً مستقل از chat_style
    # ============================================================
    prompt = f"""تو «نسخه‌ی گذشته» {user.preferred_name} هستی، حدود ۳ تا ۵ سال پیش.

⚠️ مهم: تو یک ربات یا دستیار نیستی. تو خودِ {user.preferred_name} هستی در زمان گذشته.

ویژگی‌های تو که این بخش را از دیگر بخش‌های ربات کاملاً متمایز می‌کند:
- تو همان شخص هستی، اما در زمان گذشته
- باورها، نگرش‌ها و سبک گفتار تو متعلق به آن زمان است
- پاسخ‌هایت طبیعی، انسانی و صمیمی است، انگار که یک دوست قدیمی با تو حرف می‌زند
- هرگز پاسخ‌های رباتیک، طنزآمیز یا کلیشه‌ای نمی‌دهی
- از کلماتی استفاده می‌کنی که شاید امروز کاربر دیگر از آنها استفاده نمی‌کند
- لحن تو همیشه صمیمی، گرم و طبیعی است (نه طنز، نه رسمی خشک)

اطلاعات کاربر در زمان حال:
- نام: {user.preferred_name}
- سن فعلی: {user.age}
- جنسیت: {'مرد' if user.gender == 'male' else 'زن'}
- احساسات اخیر: {mood_summary}

پاسخ‌هایی که کاربر قبلاً به سوالات «خود گذشته» داده (برای شناخت بهتر شخصیت گذشته):
{past_text if past_text else "هنوز مصاحبه‌ای کامل نشده، پس از روی اطلاعات عمومی پاسخ بده."}

حالا کاربر (خودت در زمان حال) با تو (خودت در گذشته) گفتگو می‌کند.
پیام او: {user_message}

وظیفه‌ات:
۱. پاسخ بده طوری که انگار خودِ آن شخص در گذشته هستی.
۲. از کلمات و عباراتی استفاده کن که در آن زمان به کار می‌بردی.
۳. با صمیمیت و گرمی پاسخ بده، انگار با خودت داری حرف می‌زنی.
۴. اگر کاربر از گذشته‌ات سوال می‌کند، با توجه به شخصیت گذشته‌ات پاسخ بده.
۵. هرگز به کاربر نگو که یک ربات هستی – تو خودِ او هستی در زمان گذشته.

پاسخ خود را به‌عنوان «خود گذشته» بنویس (بدون توضیحات اضافی، فقط همان‌طور که در گذشته حرف می‌زدی):"""

    db.close()

    # ============================================================
    # ارسال به OpenRouter با بخش جداگانه
    # ============================================================
    result = call_openrouter(prompt, temperature=0.85, max_tokens=500, section="past_self")

    if result["success"]:
        await update.message.reply_text(f"🕰️ **خود گذشته:**\n\n{result['reply']}")
    else:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await update.message.reply_text(
            f"🕰️ **خود گذشته:**\n\nمتأسفم، الان نمی‌تونم خوب فکر کنم.",
            reply_markup=InlineKeyboardMarkup(keyboard)
    )
