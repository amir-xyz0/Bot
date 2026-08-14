import openai
from telegram import Update
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

openai.api_key = config.OPENAI_API_KEY

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    style = user.chat_style if user else "دوستانه"
    db.close()
    
    try:
        response = openai.ChatCompletion.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"تو یک دستیار {style} هستی. با لحن {style} پاسخ بده. نام کاربر {user.preferred_name if user else 'دوست'} است."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=config.OPENAI_MAX_TOKENS
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"❌ مشکلی پیش اومد: {str(e)}")
