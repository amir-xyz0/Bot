import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

# کتابخانه پاسخ‌های از پیش‌نویس‌شده
PREDICTIONS_GOOD = [
    "🌟 امروز روز خوبی برای شروع یک کار جدید است.",
    "💪 انرژی بالایی خواهی داشت، از آن استفاده کن.",
    "😊 لبخند را فراموش نکن، امروز روزت را می‌سازد.",
    "📈 امروز یک پیشرفت کوچک اما مهم خواهی داشت.",
    "🎯 بر روی اهداف اصلی خود تمرکز کن، امروز زمان مناسبی است."
]

PREDICTIONS_BAD = [
    "🌧️ امروز ممکن است احساس خستگی کنی، به خودت استراحت بده.",
    "🛑 اگر کاری امروز پیش نرفت، به خودت سخت نگیر.",
    "🧘 یک نفس عمیق بکش و به خودت وقت بده.",
    "📝 شاید امروز بهتر باشد برنامه‌های سبک‌تری داشته باشی.",
    "💆 امروز زمان مناسبی برای مراقبت از خودت است."
]

PREDICTIONS_NEUTRAL = [
    "🌿 روز متعادلی خواهی داشت، از لحظات ساده لذت ببر.",
    "📚 امروز زمان خوبی برای مطالعه یا یادگیری است.",
    "🤝 ممکن است امروز با کسی آشنا شوی که تأثیر مثبتی دارد.",
    "🎨 خلاقیتت امروز در سطح بالایی است.",
    "🌅 از یک منظره یا لحظه‌ی ساده امروز لذت ببر."
]

async def show_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پیش‌بینی امروز بر اساس داده‌های کاربر"""
    user_id = update.effective_user.id

    if update.callback_query:
        query = update.callback_query
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

    mood_history = user.mood_history or []

    if len(mood_history) < 3:
        await message.reply_text(
            "📊 **داده‌ی کافی برای پیش‌بینی وجود ندارد.**\n\n"
            "لطفاً حداقل ۳ روز احساسات خود را ثبت کنید."
        )
        return

    # تحلیل دقیق‌تر با امتیازدهی
    recent = mood_history[-10:]  # ۱۰ روز اخیر
    good_days = sum(1 for h in recent if h.get("mood") == "good")
    bad_days = sum(1 for h in recent if h.get("mood") == "bad")

    # محاسبه امتیاز
    score = good_days * 1 - bad_days * 1.5

    # تعیین وضعیت کلی
    if score > 2:
        state = "good"
        base_predictions = PREDICTIONS_GOOD.copy()
        trend = "صعودی 📈"
    elif score < -1:
        state = "bad"
        base_predictions = PREDICTIONS_BAD.copy()
        trend = "نزولی 📉"
    else:
        state = "neutral"
        base_predictions = PREDICTIONS_NEUTRAL.copy()
        trend = "متغیر 🔄"

    # انتخاب ۲ تا ۳ پیش‌بینی تصادفی
    random.shuffle(base_predictions)
    selected = base_predictions[:2]

    # اضافه کردن یک پیش‌بینی شخصی‌سازی‌شده
    if state == "good":
        extra = "🌟 امروز بهترین نسخه‌ی خودت باش!"
    elif state == "bad":
        extra = "💪 قوی باش، این روزها هم می‌گذرند."
    else:
        extra = "🌱 هر روز یک فرصت جدید است."

    text = (
        f"🔮 **پیش‌بینی امروز**\n\n"
        f"📊 روند احساسات: {trend}\n"
        f"📅 روزهای خوب: {good_days} از {len(recent)} روز\n\n"
        f"**پیش‌بینی‌ها:**\n"
        f"• {selected[0]}\n"
        f"• {selected[1] if len(selected) > 1 else ''}\n"
        f"• {extra}\n\n"
        f"💡 این پیش‌بینی بر اساس {len(recent)} روز اخیر شماست."
    )

    keyboard = [
        [InlineKeyboardButton("🔄 پیش‌بینی فردا", callback_data="predict_tomorrow")],
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
    ]

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def predict_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیش‌بینی فردا (ویژه‌ی دکمه)"""
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    await show_prediction(update, context)
