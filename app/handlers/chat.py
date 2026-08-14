import requests
import json
from telegram import Update
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    style = user.chat_style if user else "دوستانه"
    name = user.preferred_name if user else "دوست"
    db.close()
    
    # ساخت payload دقیقاً مطابق با کد جاوا
    payload = {
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ],
        "system_prompt": f"تو یک دستیار {style} هستی. با لحن {style} پاسخ بده. نام کاربر {name} است.",
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
            # ساختار پاسخ ممکنه متفاوت باشه، اما معمولاً جواب تو کلید "choices" یا "response" هست
            # بر اساس مستندات API، احتمالاً ساختارش مثل OpenAI هست
            if "choices" in data and len(data["choices"]) > 0:
                reply = data["choices"][0]["message"]["content"]
            elif "response" in data:
                reply = data["response"]
            else:
                reply = data.get("result", "پاسخی دریافت نشد.")
            await update.message.reply_text(reply)
        else:
            error_msg = f"خطا در ارتباط با API: {response.status_code}"
            try:
                error_data = response.json()
                if "message" in error_data:
                    error_msg += f" - {error_data['message']}"
            except:
                pass
            await update.message.reply_text(f"❌ {error_msg}. لطفاً بعداً تلاش کن.")
            
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ زمان پاسخ‌دهی طولانی شد. لطفاً دوباره تلاش کن.")
    except Exception as e:
        await update.message.reply_text(f"❌ مشکلی پیش اومد: {str(e)}")
