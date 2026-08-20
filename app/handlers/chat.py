import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter

logger = logging.getLogger(__name__)

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های بخش گفتگو"""
    user_id = update.effective_user.id
    logger.info(f"🔥 chat_with_ai: user_id={user_id}")

    # ۱. بررسی ثبت‌نام
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()

    if not user:
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید. /start را بزنید.")
        return

    # ۲. بررسی بخش چت
    if context.user_data.get('current_section') != 'chat':
        await update.message.reply_text("💡 از منو، بخش «گفتگو با دستیار» را انتخاب کنید.")
        return

    # ۳. دریافت پیام کاربر
    user_message = update.message.text
    loading_msg = await update.message.reply_text("⏳ در حال پردازش...")

    # ۴. ساخت پرامپت
    prompt = f"تو یک دستیار {user.chat_style} هستی.\n\nکاربر: {user_message}"
    result = call_openrouter(prompt, temperature=0.9, max_tokens=256)

    # ۵. حذف پیام لودینگ
    try:
        await loading_msg.delete()
    except:
        pass

    # ۶. ارسال پاسخ
    if result.get("success"):
        await update.message.reply_text(result["reply"])
    else:
        await update.message.reply_text(f"❌ خطا: {result.get('error', 'مشکل ناشناخته')}")
