import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from app.openrouter_helper import call_openrouter

logger = logging.getLogger(__name__)

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # اگر پیام متنی نیست، نادیده بگیر
    if not update.message or not update.message.text:
        return
    
    # اگر پیام کامنده، نادیده بگیر
    if update.message.text.startswith('/'):
        return
    
    # فقط اگر کاربر در بخش چت باشد
    if context.user_data.get('current_section') not in [None, 'chat']:
        logger.info(f"⏭️ chat_with_ai: عبور (current_section={context.user_data.get('current_section')})")
        return

    user_id = update.effective_user.id
    logger.info(f"📩 chat_with_ai: user_id={user_id}")

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
    except Exception as e:
        logger.error(f"❌ خطا در دیتابیس: {e}")
        await update.message.reply_text("❌ خطا در ارتباط با دیتابیس.")
        db.close()
        return
    
    db.close()

    if not user:
        logger.warning(f"⚠️ کاربر {user_id} ثبت‌نام نکرده")
        await update.message.reply_text("❗ ثبت‌نام نکرده‌اید. /start را بزنید.")
        return

    user_message = update.message.text
    loading_msg = await update.message.reply_text("⏳ در حال پردازش...")

    style_map = {
        "friendly": "دوستانه، گرم و صمیمی",
        "formal": "رسمی، محترمانه و حرفه‌ای",
        "funny": "طنزآمیز، شوخ و سرگرم‌کننده",
        "calm": "آرام، متین و عمیق"
    }
    style_text = style_map.get(user.chat_style, "دوستانه و گرم")

    prompt = f"""تو یک همراه هوشمند و صمیمی هستی که با کاربری گفتگو می‌کند.
ویژگی‌های تو:
- لحن: {style_text}
- پاسخ‌هایت مختصر، مفید و دلنشین است

کاربر: {user_message}
پاسخ خود را با لحن {style_text} بنویس:"""

    result = call_openrouter(prompt, temperature=0.85, max_tokens=300, section="chat")

    try:
        await loading_msg.delete()
    except:
        pass

    if result["success"]:
        logger.info(f"✅ پاسخ ارسال شد به کاربر {user_id}")
        await update.message.reply_text(result["reply"])
    else:
        logger.error(f"❌ خطا در پاسخ به کاربر {user_id}: {result['error']}")
        await update.message.reply_text(f"❌ خطا: {result['error']}")
