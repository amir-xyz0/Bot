import requests
import json
from telegram import Update
from telegram.ext import ContextTypes
from app.config import config
from app.database import SessionLocal
from app.models import User

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔥 chat_with_ai اجرا شد!")
    user_id = update.effective_user.id
    print(f"👤 user_id: {user_id}")
    
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        print("❌ کاربر ثبت‌نام نکرده")
        await update.message.reply_text("❗ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
        return
    
    print(f"👤 کاربر: {user.preferred_name}")
    print(f"📌 current_section: {context.user_data.get('current_section')}")
    
    if context.user_data.get('current_section') != 'chat':
        print("❌ کاربر در بخش چت نیست")
        await update.message.reply_text("💡 لطفاً از منو، بخش «گفتگو با دستیار» را انتخاب کنید.")
        return
    
    user_message = update.message.text
    print(f"📩 پیام کاربر: {user_message}")
    
    # ارسال پیام لودینگ
    loading_msg = await update.message.reply_text("⏳ در حال پردازش...")
    
    try:
        # ======================================================
        # اولویت اول: GapGPT
        # ======================================================
        if config.GAPGPT_API_KEY and config.GAPGPT_API_KEY != "":
            print(f"🔑 GAPGPT_API_KEY: {config.GAPGPT_API_KEY[:10]}...")
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
                
                print(f"📤 ارسال به GapGPT...")
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                response_data = response.json()
                print(f"📥 وضعیت GapGPT: {response.status_code}")
                
                if response.status_code == 200:
                    reply = response_data.get("choices", [{}])[0].get("message", {}).get("content")
                    if reply:
                        # حذف پیام لودینگ
                        try:
                            await loading_msg.delete()
                        except:
                            pass
                        await update.message.reply_text(reply)
                        return
                else:
                    print(f"❌ خطای GapGPT: {response_data}")
                    
            except Exception as e:
                print(f"⚠️ خطا در GapGPT: {str(e)}")
        
        # ======================================================
        # اولویت دوم: RapidAPI Vision
        # ======================================================
        if config.RAPIDAPI_KEY and config.RAPIDAPI_KEY != "":
            print("🔄 تلاش با RapidAPI...")
            try:
                payload = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_message}
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
                print(f"📥 وضعیت RapidAPI: {response.status_code}")
                
                if response.status_code == 200:
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
                        try:
                            await loading_msg.delete()
                        except:
                            pass
                        await update.message.reply_text(reply)
                        return
                else:
                    print(f"❌ خطای RapidAPI: {response_data}")
                    
            except Exception as e:
                print(f"⚠️ خطا در RapidAPI: {str(e)}")
        
        # اگر هیچ پاسخی دریافت نشد
        try:
            await loading_msg.delete()
        except:
            pass
        await update.message.reply_text(
            "❌ متأسفانه هیچ پاسخی از سرور دریافت نشد.\n"
            "لطفاً چند لحظه دیگر تلاش کنید."
        )
        
    except Exception as e:
        print(f"❌ خطای کلی: {str(e)}")
        try:
            await loading_msg.delete()
        except:
            pass
        await update.message.reply_text(f"❌ خطا: {str(e)}")
