import requests
from telegram import Update
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        await update.message.reply_text(
            "❗ شما ثبت‌نام نکرده‌اید.\n"
            "لطفاً /start را بزنید و ثبت‌نام را کامل کنید."
        )
        return
    
    if context.user_data.get('current_section') != 'chat':
        await update.message.reply_text(
            "💡 لطفاً ابتدا از منوی اصلی، بخش «گفتگو با دستیار» را انتخاب کنید."
        )
        return
    
    user_message = update.message.text
    
    if not config.RAPIDAPI_KEY:
        await update.message.reply_text(
            "⚠️ متأسفانه سرویس گفتگو در حال حاضر در دسترس نیست."
        )
        return
    
    payload = {
        "messages": [{"role": "user", "content": user_message}],
        "system_prompt": f"تو یک دستیار {user.chat_style} هستی. با لحن {user.chat_style} پاسخ بده.",
        "temperature": 0.9,
        "top_k": 5,
        "top_p": 0.9,
        "max_tokens": 256,
        "web_access": False
    }
    
    headers = {
        "x-rapidapi-key": config.RAPIDAPI_KEY,
        "x-rapidapi-host": config.RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            config.CHAT_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                reply = data["choices"][0]["message"]["content"]
            elif "response" in data:
                reply = data["response"]
            else:
                reply = data.get("result", "پاسخی دریافت نشد.")
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text(
                "🔌 خطا در ارتباط با سرور. لطفاً چند لحظه دیگر تلاش کنید."
            )
    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "⏰ زمان پاسخ‌دهی طولانی شد. لطفاً دوباره تلاش کنید."
        )
    except Exception as e:
        await update.message.reply_text(
            "❌ مشکلی پیش آمد. لطفاً دوباره تلاش کنید."
        )
