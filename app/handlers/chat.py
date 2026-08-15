import requests
from telegram import Update
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('current_section') != 'chat':
        await update.message.reply_text("لطفاً ابتدا از منو، بخش گفتگو را انتخاب کنید.")
        return

    user_id = update.effective_user.id
    user_message = update.message.text

    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    style = user.chat_style if user else "friendly"
    db.close()

    payload = {
        "messages": [{"role": "user", "content": user_message}],
        "system_prompt": f"تو یک دستیار {style} هستی.",
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
        response = requests.post(config.CHAT_API_URL, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "پاسخی دریافت نشد.")
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text("خطا در ارتباط با سرور. لطفاً بعداً تلاش کنید.")
    except:
        await update.message.reply_text("مشکلی پیش آمد. دوباره تلاش کنید.")
