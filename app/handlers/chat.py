import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter

logger = logging.getLogger(__name__)

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های کاربر در بخش گفتگو"""
    logger.info("🔥 chat_with_ai: شروع")
    user_id = update.effective_user.id
    logger.info(f"👤 user_id: {user_id}")

    # ۱. چک کردن ثبت‌نام
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except Exception as e:
        logger.error(f"❌ خطا در دیتابیس: {e}")
        db.close()
        await update.message.reply_text("❌ خطایی رخ داد.")
        return
    db.close()

    if not user:
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        return

    # ۲. چک کردن بخش چت
    if context.user_data.get('current_section') != 'chat':
        await update.message.reply_text("💡 لطفاً از منو، بخش «گفتگو با دستیار» را انتخاب کنید.")
        return

    # ۳. دریافت پیام
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
    if result["success"]:
        await update.message.reply_text(result["reply"])
    else:
        await update.message.reply_text(f"❌ خطا: {result['error']}")
