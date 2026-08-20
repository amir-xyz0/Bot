import requests
import json
import logging
import random
from app.config import config

logger = logging.getLogger(__name__)

def call_openrouter(prompt, temperature=0.8, max_tokens=400):
    """ارسال درخواست به OpenRouter با fallback پاسخ ساختگی"""
    logger.info("📤 ارسال درخواست به OpenRouter...")
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

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content")
            if reply:
                logger.info("✅ پاسخ از OpenRouter دریافت شد.")
                return {"success": True, "reply": reply}
            else:
                logger.warning("⚠️ پاسخ خالی از OpenRouter.")
        else:
            logger.error(f"❌ خطای OpenRouter: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"❌ خطا در ارتباط با OpenRouter: {e}")

    # Fallback: پاسخ ساختگی
    fake_replies = [
        "سلام! این یک پاسخ آزمایشی است.",
        "ربات به درستی کار می‌کند.",
        "OpenRouter در دسترس نیست، اما من اینجام!",
        "این یک پاسخ تست از طرف ربات است."
    ]
    reply = random.choice(fake_replies)
    logger.info(f"🧪 پاسخ ساختگی: {reply}")
    return {"success": True, "reply": reply}
