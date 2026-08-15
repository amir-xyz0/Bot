import requests
import json
from telegram import Update
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # چک کردن ثبت‌نام
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        await update.message.reply_text(
            "❗ شما ثبت‌نام نکرده‌اید.\n"
            "لطفاً /start را بزنید."
        )
        return
    
    # چک کردن بخش چت
    if context.user_data.get('current_section') != 'chat':
        await update.message.reply_text(
            "💡 لطفاً از منو، بخش «گفتگو با دستیار» را انتخاب کنید."
        )
        return
    
    user_message = update.message.text
    await update.message.reply_text("⏳ در حال پردازش...")
    
    # چک کردن کلید API
    if not config.RAPIDAPI_KEY or config.RAPIDAPI_KEY == "":
        await update.message.reply_text(
            "⚠️ کلید API تنظیم نشده است.\n"
            "لطفاً متغیر `RAPIDAPI_KEY` را در Render تنظیم کنید."
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
        # ارسال درخواست
        response = requests.post(
            config.CHAT_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # دریافت پاسخ
        response_data = response.json()
        
        # بررسی وضعیت
        if response.status_code != 200:
            error_msg = response_data.get("message", "خطای ناشناخته")
            await update.message.reply_text(
                f"❌ خطای سرور ({response.status_code}):\n{error_msg}"
            )
            return
        
        # استخراج پاسخ
        reply = None
        if "choices" in response_data and len(response_data["choices"]) > 0:
            reply = response_data["choices"][0].get("message", {}).get("content")
        elif "response" in response_data:
            reply = response_data["response"]
        elif "result" in response_data:
            reply = response_data["result"]
        elif "text" in response_data:
            reply = response_data["text"]
        elif "data" in response_data:
            data = response_data["data"]
            if isinstance(data, dict) and "text" in data:
                reply = data["text"]
        
        if reply:
            await update.message.reply_text(reply)
        else:
            # نمایش پاسخ خام برای دیباگ
            await update.message.reply_text(
                f"⚠️ پاسخ غیرمنتظره:\n```json\n{json.dumps(response_data, indent=2, ensure_ascii=False)}\n```"
            )
            
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ زمان پاسخ‌دهی طولانی شد. لطفاً دوباره تلاش کنید.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("🔌 اتصال به سرور برقرار نشد. لطفاً بعداً تلاش کنید.")
    except json.JSONDecodeError:
        await update.message.reply_text("⚠️ پاسخ سرور معتبر نیست.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
