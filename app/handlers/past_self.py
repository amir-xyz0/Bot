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

# سوالات عمیق و علمی برای مصاحبه با گذشته
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

    try:
        past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else None
    except:
        past_answers = None

    if past_answers and len(past_answers) > 0:
        keyboard = [
            [InlineKeyboardButton("📋 دیدن پاسخ‌های قبلی", callback_data="past_self_show_answers")],
            [InlineKeyboardButton("🔄 مصاحبه‌ی جدید", callback_data="past_self_new_interview")],
            [InlineKeyboardButton("💬 گفتگوی آزاد", callback_data="past_self_free_chat")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ]
        await message.reply_text(
            "🕰️ **خود گذشته**\n\nشما قبلاً در مصاحبه شرکت کرده‌اید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        db.close()
        return

    context.user_data['past_self_mode'] = True
    context.user_data['past_self_step'] = 0
    context.user_data['past_self_answers'] = []
    db.close()
    await send_next_question(update, context)

async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال سوال بعدی مصاحبه"""
    step = context.user_data.get('past_self_step', 0)
    if step >= len(PAST_QUESTIONS):
        await finish_interview(update, context)
        return

    q = PAST_QUESTIONS[step]
    text = (
        f"🕰️ **مصاحبه با گذشته – سوال {step+1} از {len(PAST_QUESTIONS)}**\n\n"
        f"{q['question']}\n\n✍️ پاسخ خود را بنویسید:"
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

async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت پاسخ کاربر – فقط در حالت مصاحبه"""
    if not context.user_data.get('past_self_mode'):
        return

    user_id = update.effective_user.id
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
    """پایان مصاحبه و ذخیره پاسخ‌ها"""
    user_id = update.effective_user.id
    answers = context.user_data.get('past_self_answers', [])

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if user:
            user.personality_profile = answers
            db.commit()
    except Exception as e:
        logger.error(f"خطا در ذخیره: {e}")
    finally:
        db.close()

    context.user_data['past_self_mode'] = False
    context.user_data['past_self_step'] = 0

    text = f"✅ **مصاحبه کامل شد!**\n\nشما به {len(answers)} سوال پاسخ دادید."
    keyboard = [
        [InlineKeyboardButton("📋 دیدن پاسخ‌ها", callback_data="past_self_show_answers")],
        [InlineKeyboardButton("💬 گفتگوی آزاد", callback_data="past_self_free_chat")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
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
    """نمایش پاسخ‌های ذخیره‌شده"""
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
    text = "📋 **پاسخ‌های شما:**\n\n"
    for i, item in enumerate(answers, 1):
        q = item.get("question", "سوال")
        a = item.get("answer", "پاسخ")
        a_short = a[:60] + "..." if len(a) > 60 else a
        text += f"{i}. {q}\n   📝 {a_short}\n\n"
        if len(text) > 3500:
            text += "\n... و بقیه"
            break

    keyboard = [
        [InlineKeyboardButton("💬 گفتگوی آزاد", callback_data="past_self_free_chat")],
        [InlineKeyboardButton("🔄 مصاحبه جدید", callback_data="past_self_new_interview")],
        [InlineKeyboardButton("🗑️ پاک کردن", callback_data="past_self_delete_answers")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="past_self_menu")]
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
        logger.error(f"خطا: {e}")
    finally:
        db.close()

    await query.edit_message_text(
        "✅ پاسخ‌ها پاک شد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 مصاحبه جدید", callback_data="past_self_new_interview")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
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
        logger.error(f"خطا: {e}")
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

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
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
        await query.edit_message_text("❗ ثبت‌نام نکرده‌اید.")
        db.close()
        return

    context.user_data['past_self_mode'] = True
    context.user_data['past_self_free_chat'] = True

    try:
        await query.message.delete()
    except:
        pass

    text = "💬 **گفتگوی آزاد با گذشته**\n\nسوالات خود را بپرسید.\nبرای پایان، دکمه زیر را بزنید."
    keyboard = [[InlineKeyboardButton("🔚 پایان گفتگو", callback_data="past_self_end_free_chat")]]
    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    db.close()

async def end_free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['past_self_mode'] = False
    context.user_data['past_self_free_chat'] = False

    try:
        await query.message.delete()
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
    await query.message.reply_text("✅ گفتگوی آزاد پایان یافت.", reply_markup=InlineKeyboardMarkup(keyboard))

async def chat_with_past_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش گفتگوی آزاد با هوش مصنوعی"""
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
        db.close()
        return

    past_answers = user.personality_profile if hasattr(user, 'personality_profile') and user.personality_profile else []

    past_text = ""
    if past_answers and len(past_answers) > 0:
        for item in past_answers[:3]:
            past_text += f"- {item.get('question', '')}\n  پاسخ: {item.get('answer', '')[:80]}...\n"

    prompt = f"""تو یک همراه صمیمی هستی که با کاربر درباره‌ی گذشته‌اش گفتگو می‌کند.

نام: {user.preferred_name}
سن: {user.age}
پاسخ‌های قبلی به مصاحبه:
{past_text if past_text else "مصاحبه‌ای کامل نشده است."}

پیام کاربر: {user_message}

پاسخ خود را به‌عنوان یک همراه صمیمی بنویس (با لحنی گرم و همدلانه):
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
        logger.error(f"خطا: {e}")

    await update.message.reply_text("🕰️ **همراه گذشته:**\n\nمتأسفم، الان نمی‌تونم خوب فکر کنم.")
    db.close()
