import logging
import random

logger = logging.getLogger(__name__)

def call_openrouter(prompt, temperature=0.8, max_tokens=400):
    """
    حالت تست: به جای OpenRouter، یک پاسخ تصادفی برمی‌گرداند
    """
    logger.info("=" * 50)
    logger.info("🧪 حالت تست: استفاده از پاسخ ساختگی")
    logger.info(f"📝 پرامپت: {prompt[:100]}...")
    
    # لیست پاسخ‌های ساختگی
    fake_responses = [
        "سلام! چطور می‌توانم به شما کمک کنم؟",
        "این یک پاسخ آزمایشی از ربات است.",
        "OpenRouter در حال حاضر در دسترس نیست، اما من اینجام!",
        "ربات به درستی کار می‌کند. این یک پاسخ تست است.",
        "تبریک! ربات شما به درستی راه‌اندازی شده است."
    ]
    
    reply = random.choice(fake_responses)
    logger.info(f"✅ پاسخ ساختگی: {reply}")
    
    return {"success": True, "reply": reply}
