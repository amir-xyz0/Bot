import requests
import json
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
            "لطفاً /start را بزنید."
        )
        return
    
    if context.user_data.get('current_section') != 'chat':
        await update.message.reply_text(
            "💡 لطفاً از منو، بخش گفتگو را انتخاب کنید."
        )
        return
    
    user_message = update.message.text
    
    # چک کردن کلید API
    if not config.RAPIDAPI_KEY:
        await update.message.reply_text(
            "⚠️ متأسفانه سرویس گفتگو در دسترس نیست. (کلید API تنظیم نشده)"
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
        # ارسال درخواست به API
        response = requests.post(
            config.CHAT_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # دریافت پاسخ
        response_data = response.json()
        
        # نمایش خطای دقیق در صورت وجود
        if response.status_code != 200:
            error_msg = response_data.get("message", "خطای ناشناخته")
            await update.message.reply_text(
                f"❌ خطای سرور ({response.status_code}):\n{error_msg}"
            )
            return
        
        # استخراج پاسخ از ساختارهای مختلف
        reply = None
        if "choices" in response_data and len(response_data["choices"]) > 0:
            reply = response_data["choices"][0].get("message", {}).get("content")
        elif "response" in response_data:
            reply = response_data["response"]
        elif "result" in response_data:
            reply = response_data["result"]
        elif "text" in response_data:
            reply = response_data["text"]
        
        if reply:
            await update.message.reply_text(reply)
        else:
            await update.message.reply_text(
                f"⚠️ پاسخ غیرمنتظره از سرور:\n```json\n{json.dumps(response_data, indent=2, ensure_ascii=False)}\n```"
            )
            
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ زمان پاسخ‌دهی طولانی شد. لطفاً دوباره تلاش کنید.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("🔌 اتصال به سرور برقرار نشد.")
    except json.JSONDecodeError:
        await update.message.reply_text("⚠️ پاسخ سرور معتبر نیست.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
