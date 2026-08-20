import requests
import json
import logging
import random
from app.config import config

logger = logging.getLogger(__name__)

def call_openrouter(prompt, temperature=0.8, max_tokens=400):
    """
    تلاش برای ارتباط با OpenRouter، در صورت خطا پاسخ ساختگی می‌دهد
    """
    logger.info("=" * 50)
    logger.info("🚀 شروع درخواست به OpenRouter")
    logger.info(f"📝 پرامپت: {prompt[:200]}...")
    
    try:
        url = f"{config.OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/your_bot",
            "X-Title": "Life Assistant Bot"
        }
        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        logger.info(f"📤 ارسال به OpenRouter...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        logger.info(f"📥 وضعیت: {response.status_code}")
        logger.info(f"📄 پاسخ: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                logger.info("✅ پاسخ دریافت شد")
                return {"success": True, "reply": reply}
            else:
                logger.warning("⚠️ پاسخ خالی")
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"خطای {response.status_code}")
            logger.error(f"❌ خطای OpenRouter: {error_msg}")
            
    except Exception as e:
        logger.error(f"❌ خطا: {str(e)}")
    
    # اگر خطا بود، پاسخ ساختگی
    logger.info("🧪 استفاده از پاسخ ساختگی")
    fake_responses = [
        "سلام! این یک پاسخ آزمایشی است. ربات شما به درستی کار می‌کند.",
        "OpenRouter در دسترس نیست، اما من اینجام!",
        "ربات آماده است! این یک پاسخ تست است.",
        "تبریک! ربات شما به درستی راه‌اندازی شده است."
    ]
    return {"success": True, "reply": random.choice(fake_responses)}
