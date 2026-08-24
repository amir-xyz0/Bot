import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter

logger = logging.getLogger(__name__)

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
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(
            "❗ ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    context.user_data['current_section'] = 'past_self'
    logger.info(f"🕰️ start_past_self: user_id={user_id}")

    keyboard = [
        [InlineKeyboardButton("📋 مصاحبه‌ی جدید", callback_data="past_self_new_interview")],
        [InlineKeyboardButton("💬 گفتگوی آزاد", callback_data="past_self_free_chat")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
    ]
    await message.reply_text(
        "🕰️ **آیینه‌ی گذشته**\n\n"
        "می‌توانی با نسخه‌ی گذشته‌ات گفتگو کنی.\n"
        "• با «مصاحبه» شروع کن تا بیشتر بهت کمک کنم.\n"
        "• یا مستقیم «گفتگوی آزاد» رو انتخاب کن.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def new_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['past_self_mode'] = True
    context.user_data['past_self_step'] = 0
    context.user_data['past_self_answers'] = []
    context.user_data['past_self_free_chat'] = False
    
    await send_next_question(update, context)

async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('past_self_step', 0)
    
    if step >= len(PAST_QUESTIONS):
        await finish_interview(update, context)
        return

    question_data = PAST_QUESTIONS[step]
    text = (
        f"🕰️ **مصاحبه با گذشته – سوال {step+1} از {len(PAST_QUESTIONS)}**\n\n"
        f"{question_data['question']}\n\n"
        f"✍️ پاسخ خود را بنویسید:"
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

async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if update.message.text.startswith('/'):
        return
    
    if context.user_data.get('current_section') != 'past_self':
        return
    if not context.user_data.get('past_self_mode'):
        return
    if context.user_data.get('past_self_free_chat'):
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

async def finish_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answers = context.user_data.get('past_self_answers', [])

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.personality_profile = answers
            db.commit()
            logger.info(f"✅ پاسخ‌های کاربر {user_id} ذخیره شد")
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره پاسخ‌ها: {e}")
    finally:
        db.close()

    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0

    text = (
        "✅ **مصاحبه کامل شد!**\n\n"
        f"شما به {len(answers)} سوال پاسخ دادید.\n"
        "حالا می‌توانید «گفتگوی آزاد» رو شروع کنید."
    )

    keyboard = [
        [InlineKeyboardButton("💬 گفتگوی آزاد", callback_data="past_self_free_chat")],
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

async def free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()

    if not user:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await query.edit_message_text(
            "❗ ثبت‌نام نکرده‌اید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    context.user_data['current_section'] = 'past_self'
    context.user_data['past_self_mode'] = True
    context.user_data['past_self_free_chat'] = True

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [
        [InlineKeyboardButton("🔚 پایان گفتگو", callback_data="past_self_end_free_chat")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
    ]
    await query.message.reply_text(
        "🕰️ **گفتگوی آزاد با گذشته**\n\n"
        "هر سوالی داری از خودت در گذشته بپرس.\n"
        "مثلاً: «چرا اون تصمیم رو گرفتی؟»",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def chat_with_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if update.message.text.startswith('/'):
        return
    
    if context.user_data.get('current_section') != 'past_self':
        return
    if not context.user_data.get('past_self_mode') or not context.user_data.get('past_self_free_chat'):
        return

    user_id = update.effective_user.id
    user_message = update.message.text
    logger.info(f"💬 chat_with_past_self: user_id={user_id}")

    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()

    if not user:
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید.")
        return

    past_answers = user.personality_profile or []
    past_text = ""
    for item in past_answers[:5]:
        past_text += f"- {item.get('question', '')}\n  پاسخ: {item.get('answer', '')[:100]}...\n"

    prompt = f"""تو «نسخه‌ی گذشته» {user.preferred_name} هستی، حدود ۳ تا ۵ سال پیش.

تو خودِ {user.preferred_name} هستی در زمان گذشته.
باورها، نگرش‌ها و سبک گفتار تو متعلق به آن زمان است.
پاسخ‌هایت طبیعی، انسانی و صمیمی است.

اطلاعات کاربر در زمان حال:
- نام: {user.preferred_name}
- سن فعلی: {user.age}

پاسخ‌های قبلی کاربر:
{past_text if past_text else "هنوز مصاحبه‌ای کامل نشده."}

حالا کاربر (خودت در زمان حال) با تو (خودت در گذشته) گفتگو می‌کند.
پیام او: {user_message}

پاسخ خود را به‌عنوان «خود گذشته» بنویس (فقط پاسخ، بدون توضیحات اضافی):"""

    result = call_openrouter(prompt, temperature=0.85, max_tokens=500, section="past_self")

    if result["success"]:
        await update.message.reply_text(f"🕰️ **خود گذشته:**\n\n{result['reply']}")
    else:
        await update.message.reply_text("🕰️ متأسفم، الان نمی‌تونم خوب فکر کنم.")

async def end_free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['current_section'] = None
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_free_chat'] = False

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text(
        "✅ **گفتگوی آزاد به پایان رسید.**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def end_interview_early(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text(
        "⏹️ **مصاحبه نیمه‌کاره ماند.**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
