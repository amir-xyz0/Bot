import requests
import logging
from app.config import config

logger = logging.getLogger(__name__)

def call_openrouter(prompt, temperature=0.8, max_tokens=400, section="general"):
    """
    ارسال درخواست به OpenRouter
    section: chat, therapist, past_self, predictor
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

        logger.info(f"📤 ارسال به OpenRouter (بخش: {section})...")
        logger.info(f"📤 طول پرامپت: {len(prompt)} کاراکتر")
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)

        logger.info(f"📥 پاسخ OpenRouter: status={response.status_code}")

        if response.status_code == 200:
            data = response.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                logger.info(f"✅ پاسخ از OpenRouter دریافت شد (بخش: {section})")
                logger.info(f"✅ طول پاسخ: {len(reply)} کاراکتر")
                return {"success": True, "reply": reply}
            else:
                logger.error("❌ پاسخ خالی از OpenRouter")
                return {"success": False, "error": "پاسخ خالی"}
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"خطای {response.status_code}")
            logger.error(f"❌ خطای OpenRouter: {error_msg}")
            return {"success": False, "error": error_msg}

    except requests.exceptions.Timeout:
        logger.error("❌ Timeout در OpenRouter")
        return {"success": False, "error": "زمان پاسخدهی طولانی شد"}
    except requests.exceptions.ConnectionError:
        logger.error("❌ ConnectionError در OpenRouter")
        return {"success": False, "error": "اتصال به سرور برقرار نشد"}
    except Exception as e:
        logger.error(f"❌ خطای ناشناخته در OpenRouter: {e}")
        return {"success": False, "error": str(e)}
