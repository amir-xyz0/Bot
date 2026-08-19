import requests
import json
import logging
from app.config import config

logger = logging.getLogger(__name__)

def call_openrouter(prompt, temperature=0.8, max_tokens=400):
    """
    تابع کمکی برای ارسال درخواست به OpenRouter و دریافت پاسخ
    این تابع همه خطاها را مدیریت می‌کند و همیشه یک پاسخ برمی‌گرداند
    """
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
        
        logger.info(f"📥 وضعیت OpenRouter: {response.status_code}")
        logger.info(f"📄 پاسخ OpenRouter: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                return {"success": True, "reply": reply}
            else:
                logger.warning("⚠️ پاسخ خالی از OpenRouter")
                return {"success": False, "error": "پاسخ خالی"}
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"خطای {response.status_code}")
            logger.error(f"❌ خطای OpenRouter: {error_msg}")
            return {"success": False, "error": error_msg}
            
    except requests.exceptions.Timeout:
        logger.error("⏰ زمان پاسخ‌دهی طولانی شد")
        return {"success": False, "error": "زمان پاسخ‌دهی طولانی شد"}
    except requests.exceptions.ConnectionError:
        logger.error("🔌 اتصال به سرور برقرار نشد")
        return {"success": False, "error": "اتصال به سرور برقرار نشد"}
    except json.JSONDecodeError as e:
        logger.error(f"❌ خطا در پردازش JSON: {e}")
        return {"success": False, "error": "پاسخ سرور معتبر نیست"}
    except Exception as e:
        logger.error(f"❌ خطا: {str(e)}")
        return {"success": False, "error": str(e)}
