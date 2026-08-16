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
    
    # ======================================================
    #  اولویت اول: GapGPT
    # ======================================================
    if config.GAPGPT_API_KEY and config.GAPGPT_API_KEY != "":
        try:
            url = f"{config.GAPGPT_BASE_URL}/chat/completions"
            headers = {
                "Authorization": f"Bearer {config.GAPGPT_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": config.GAPGPT_MODEL,
                "messages": [
                    {"role": "system", "content": f"تو یک دستیار {user.chat_style} هستی. با لحن {user.chat_style} پاسخ بده."},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.9,
                "max_tokens": 256
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200:
                reply = response_data.get("choices", [{}])[0].get("message", {}).get("content")
                if reply:
                    await update.message.reply_text(reply)
                    return
                else:
                    await update.message.reply_text(
                        f"⚠️ پاسخ خالی از GapGPT:\n```json\n{json.dumps(response_data, indent=2, ensure_ascii=False)[:500]}\n```"
                    )
                    # در صورت خالی بودن پاسخ، به سراغ RapidAPI می‌رویم
            else:
                error_msg = response_data.get("error", {}).get("message", "خطای ناشناخته")
                await update.message.reply_text(
                    f"❌ خطای GapGPT ({response.status_code}):\n{error_msg}\n\nتلاش با RapidAPI..."
                )
                # ادامه به سراغ RapidAPI
                
        except Exception as e:
            await update.message.reply_text(
                f"⚠️ خطا در GapGPT: {str(e)}\n\nتلاش با RapidAPI..."
            )
            # ادامه به سراغ RapidAPI
    else:
        await update.message.reply_text("⏳ کلید GapGPT تنظیم نشده، تلاش با RapidAPI...")
    
    # ======================================================
    #  اولویت دوم: RapidAPI Vision (با همان کلید قبلی)
    # ======================================================
    if not config.RAPIDAPI_KEY or config.RAPIDAPI_KEY == "":
        await update.message.reply_text(
            "❌ هیچ کلید API فعالی تنظیم نشده است!\n"
            "لطفاً `GAPGPT_API_KEY` یا `RAPIDAPI_KEY` را در Render تنظیم کنید."
        )
        return
    
    try:
        # ساخت payload مطابق با API Vision
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ]
                }
            ],
            "web_access": False
        }
        
        headers = {
            "x-rapidapi-key": config.RAPIDAPI_KEY,
            "x-rapidapi-host": config.RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            config.CHAT_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response_data = response.json()
        
        if response.status_code == 200:
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
            elif "data" in response_data and isinstance(response_data["data"], dict):
                reply = response_data["data"].get("text") or response_data["data"].get("response")
            
            if reply:
                await update.message.reply_text(reply)
            else:
                await update.message.reply_text(
                    f"⚠️ پاسخ غیرمنتظره از RapidAPI:\n```json\n{json.dumps(response_data, indent=2, ensure_ascii=False)[:1000]}\n```"
                )
        else:
            error_msg = response_data.get("message", response_data.get("error", "خطای ناشناخته"))
            await update.message.reply_text(
                f"❌ خطای RapidAPI ({response.status_code}):\n{error_msg}"
            )
            
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ زمان پاسخ‌دهی طولانی شد. لطفاً دوباره تلاش کنید.")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("🔌 اتصال به سرور برقرار نشد. لطفاً بعداً تلاش کنید.")
    except json.JSONDecodeError:
        await update.message.reply_text("⚠️ پاسخ سرور معتبر نیست.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
