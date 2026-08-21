import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

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
        await message.reply_text(
            "❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        db.close()
        return

    # ✅ تنظیم current_section برای جلوگیری از تداخل با گفتگو
    context.user_data['current_section'] = 'past_self'

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
            "شما قبلاً در مصاحبه‌ای شرکت کرده‌اید.\n\n"
            "• می‌توانید پاسخ‌های قبلی را مرور کنید.\n"
            "• مصاحبه‌ی جدیدی شروع کنید.\n"
            "• یا با نسخه‌ی گذشته‌ی خود گفتگو کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    context.user_data['past_self_mode'] = True
    context.user_data['past_self_step'] = 0
    context.user_data['past_self_answers'] = []
    await send_next_question(update, context)

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

async def finish_interview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answers = context.user_data.get('past_self_answers', [])

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.personality_profile = answers
            db.commit()
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
    finally:
        db.close()

    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0
    context.user_data['current_section'] = None  # ✅ پاک کردن current_section

    text = f"✅ **مصاحبه کامل شد!**\n\nشما به {len(answers)} سوال پاسخ دادید."
    keyboard = [
        [InlineKeyboardButton("📋 دیدن پاسخ‌ها", callback_data="past_self_show_answers")],
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
        await query.edit_message_text(
            "📭 شما هنوز مصاحبه‌ای کامل نکرده‌اید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        db.close()
        return

    answers = user.personality_profile
    text = "📋 **پاسخ‌های شما:**\n\n"
    for i, item in enumerate(answers, 1):
        q = item.get("question", "سوال")
        a = item.get("answer", "پاسخ")[:60] + "..." if len(item.get("answer", "")) > 60 else item.get("answer", "پاسخ")
        text += f"{i}. {q}\n   📝 {a}\n\n"
        if len(text) > 3500:
            text += "\n... و بقیه"
            break

    keyboard = [
        [InlineKeyboardButton("💬 گفتگوی آزاد", callback_data="past_self_free_chat")],
        [InlineKeyboardButton("🔄 مصاحبه جدید", callback_data="past_self_new_interview")],
        [InlineKeyboardButton("🗑️ پاک کردن", callback_data="past_self_delete_answers")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    db.close()

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
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
    finally:
        db.close()

    await query.edit_message_text(
        "✅ پاسخ‌ها پاک شد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 مصاحبه جدید", callback_data="past_self_new_interview")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
        ])
    )

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

async def end_interview_early(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0
    context.user_data['current_section'] = None  # ✅ پاک کردن current_section

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text("⏹️ مصاحبه پایان یافت.", reply_markup=InlineKeyboardMarkup(keyboard))

async def free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "❗ ثبت‌نام نکرده‌اید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        db.close()
        return

    # ✅ تنظیم current_section برای جلوگیری از تداخل با گفتگو
    context.user_data['current_section'] = 'past_self'
    context.user_data['past_self_mode'] = True
    context.user_data['past_self_free_chat'] = True

    try:
        await query.message.delete()
    except:
        pass

    text = "💬 **گفتگوی آزاد با گذشته**\n\nسوالات خود را بپرسید.\nبرای پایان، دکمه زیر را بزنید."
    keyboard = [
        [InlineKeyboardButton("🔚 پایان گفتگو", callback_data="past_self_end_free_chat")],
        [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]
    ]
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    db.close()

async def end_free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_free_chat'] = False
    context.user_data['current_section'] = None  # ✅ پاک کردن current_section

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
    await query.message.reply_text("✅ گفتگوی آزاد پایان یافت.", reply_markup=InlineKeyboardMarkup(keyboard))

async def chat_with_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    past_text = ""
    if past_answers and len(past_answers) > 0:
        for item in past_answers[:5]:
            past_text += f"- {item.get('question', '')}\n  پاسخ: {item.get('answer', '')[:120]}...\n"

    # ============================================================
    # پرامپت مستقل – بدون هیچ ارجاعی به chat_style
    # ============================================================
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

پاسخ‌های کاربر به سوالات گذشته:
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
