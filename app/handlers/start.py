import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"🔥 start: user_id={user_id}")

    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()

    context.user_data.clear()

    if user:
        from app.handlers.menu import main_menu
        await main_menu(update, context)
        return

    # ✅ حذف پیام دیسکریپشن (بیو) بعد از کلیک روی دکمه شروع
    # این پیام خودکار توسط تلگرام ارسال شده، اما ما پیام جدیدی می‌فرستیم و پیام قبلی را حذف می‌کنیم
    try:
        await update.message.delete()
    except:
        pass

    text = (
        "✨ **به «همراه روزمره‌ات» خوش آمدی!** ✨\n\n"
        "من اینجام تا روزهایت را سبک‌تر، زیباتر و هدف‌مندتر کنم.\n"
        "با هم مسیر رشد، آرامش و شادی را می‌سازیم.\n\n"
        "🌱 **برای شروع، بیا کمی بیشتر همدیگر را بشناسیم...**"
    )
    keyboard = [[InlineKeyboardButton("🌟 شروع ثبت‌نام", callback_data="start_profile")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
