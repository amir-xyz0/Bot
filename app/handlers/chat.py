import requests
import json
import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger(__name__)

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔥 chat_with_ai اجرا شد!")
    
    user_id = update.effective_user.id
    
    # ✅ ایجاد Session جدید برای هر درخواست
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except Exception as e:
        logger.error(f"❌ خطا در دیتابیس: {e}")
        db.close()
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        return
    db.close()
    
    if not user:
        await update.message.reply_text("❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        return
    
    # ✅ دسترسی به attributes بعد از بسته شدن سشن مشکلی ندارد چون expire_on_commit=False است
    user_name = user.preferred_name
    user_style = user.chat_style
    
    if context.user_data.get('current_section') != 'chat':
        await update.message.reply_text("💡 لطفاً از منو، بخش «گفتگو با دستیار» را انتخاب کنید.")
        return
    
    user_message = update.message.text
    loading_msg = await update.message.reply_text("⏳ در حال پردازش...")
    
    try:
        url = f"{config.OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": f"تو یک دستیار {user_style} هستی. با لحن {user_style} پاسخ بده."},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.9,
            "max_tokens": 256
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json()
        logger.info(f"📥 وضعیت OpenRouter: {response.status_code}")
        
        if response.status_code == 200:
            reply = response_data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                await loading_msg.delete()
                await update.message.reply_text(reply)
                return
        else:
            error_msg = response_data.get("error", {}).get("message", "خطای ناشناخته")
            await loading_msg.delete()
            await update.message.reply_text(f"❌ خطا: {error_msg}")
            
    except requests.exceptions.Timeout:
        await loading_msg.delete()
        await update.message.reply_text("⏰ زمان پاسخ‌دهی طولانی شد. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        logger.error(f"❌ خطا: {str(e)}")
        await loading_msg.delete()
        await update.message.reply_text(f"❌ خطا: {str(e)}")
