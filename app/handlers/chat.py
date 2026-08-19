import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter

logger = logging.getLogger(__name__)

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
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
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید. /start را بزنید.")
        return
    
    if context.user_data.get('current_section') != 'chat':
        await update.message.reply_text("💡 از منو، بخش «گفتگو با دستیار» را انتخاب کنید.")
        return
    
    user_message = update.message.text
    loading_msg = await update.message.reply_text("⏳ در حال پردازش...")
    
    prompt = f"تو یک دستیار {user.chat_style} هستی.\n\nکاربر: {user_message}"
    result = call_openrouter(prompt, temperature=0.9, max_tokens=256)
    
    await loading_msg.delete()
    
    if result["success"]:
        await update.message.reply_text(result["reply"])
    else:
        await update.message.reply_text(f"❌ خطا: {result['error']}")
