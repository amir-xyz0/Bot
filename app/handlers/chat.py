import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter

logger = logging.getLogger(__name__)

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔥 chat_with_ai اجرا شد!")
    user_id = update.effective_user.id
    logger.info(f"👤 user_id: {user_id}")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except Exception as e:
        logger.error(f"❌ دیتابیس: {e}")
        db.close()
        await update.message.reply_text("❌ خطایی رخ داد.")
        return
    db.close()
    
    if not user:
        logger.warning("❌ کاربر ثبت‌نام نکرده")
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید. /start را بزنید.")
        return
    
    logger.info(f"👤 کاربر: {user.preferred_name}")
    logger.info(f"📌 current_section: {context.user_data.get('current_section')}")
    
    if context.user_data.get('current_section') != 'chat':
        logger.warning("❌ کاربر در بخش چت نیست")
        await update.message.reply_text("💡 از منو، بخش «گفتگو با دستیار» را انتخاب کنید.")
        return
    
    user_message = update.message.text
    logger.info(f"📩 پیام کاربر: {user_message[:50]}...")
    loading_msg = await update.message.reply_text("⏳ در حال پردازش...")
    
    prompt = f"تو یک دستیار {user.chat_style} هستی.\n\nکاربر: {user_message}"
    result = call_openrouter(prompt, temperature=0.9, max_tokens=256)
    
    await loading_msg.delete()
    
    if result["success"]:
        logger.info("✅ پاسخ دریافت شد")
        await update.message.reply_text(result["reply"])
    else:
        logger.error(f"❌ خطا: {result['error']}")
        await update.message.reply_text(f"❌ خطا: {result['error']}")
