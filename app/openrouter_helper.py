import requests
import logging
from app.config import config

logger = logging.getLogger(__name__)

def call_openrouter(prompt, temperature=0.8, max_tokens=400, section="general"):
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
                return {"success": True, "reply": reply}
            else:
                return {"success": False, "error": "پاسخ خالی"}
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"خطای {response.status_code}")
            return {"success": False, "error": error_msg}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "زمان پاسخ‌دهی طولانی شد"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "اتصال به سرور برقرار نشد"}
    except Exception as e:
        return {"success": False, "error": str(e)}
