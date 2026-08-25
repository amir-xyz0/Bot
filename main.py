import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from app.config import config
from app.handlers import (
    start, profile, menu, chat, history, profile_edit,
    predictor, past_self, therapist
)
from app.database import Base, engine
from app.scheduler import start_scheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="⚠️ خطا:", exc_info=context.error)
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass

app = ApplicationBuilder().token(config.BOT_TOKEN).build()

# ============================================================
# CommandHandlerها
# ============================================================
app.add_handler(CommandHandler("start", start.start))
app.add_handler(CommandHandler("menu", menu.main_menu))

# ============================================================
# ConversationHandler ثبت‌نام - فعال
# ============================================================
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(profile.start_profile, pattern="start_profile")],
    states={
        profile.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_name)],
        profile.GENDER: [CallbackQueryHandler(profile.get_gender)],
        profile.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile.get_age)],
        profile.STYLE: [CallbackQueryHandler(profile.get_style)]
    },
    fallbacks=[CommandHandler("start", start.start)],
    per_message=False
)
app.add_handler(conv_handler)

# ============================================================
# CallbackQueryHandlerها
# ============================================================
app.add_handler(CallbackQueryHandler(profile.start_profile, pattern="start_profile"))
app.add_handler(CallbackQueryHandler(profile.get_gender, pattern="^gender_"))
app.add_handler(CallbackQueryHandler(profile.get_style, pattern="^style_"))

app.add_handler(CallbackQueryHandler(menu.main_menu, pattern="main_menu"))
app.add_handler(CallbackQueryHandler(menu.chat_menu, pattern="chat_menu"))
app.add_handler(CallbackQueryHandler(menu.therapy_menu, pattern="therapy_menu"))
app.add_handler(CallbackQueryHandler(menu.past_self_menu, pattern="past_self_menu"))
app.add_handler(CallbackQueryHandler(menu.predict_menu, pattern="predict_menu"))
app.add_handler(CallbackQueryHandler(menu.history_menu, pattern="history_menu"))
app.add_handler(CallbackQueryHandler(menu.profile_menu, pattern="profile_menu"))

app.add_handler(CallbackQueryHandler(therapist.start_therapy, pattern="therapy_menu"))
app.add_handler(CallbackQueryHandler(therapist.end_therapy, pattern="end_therapy"))

app.add_handler(CallbackQueryHandler(past_self.start_past_self, pattern="past_self_menu"))
app.add_handler(CallbackQueryHandler(past_self.show_answers, pattern="past_self_show_answers"))
app.add_handler(CallbackQueryHandler(past_self.delete_answers, pattern="past_self_delete_answers"))
app.add_handler(CallbackQueryHandler(past_self.new_interview, pattern="past_self_new_interview"))
app.add_handler(CallbackQueryHandler(past_self.end_interview_early, pattern="past_self_end_interview"))
app.add_handler(CallbackQueryHandler(past_self.free_chat, pattern="past_self_free_chat"))
app.add_handler(CallbackQueryHandler(past_self.end_free_chat, pattern="past_self_end_free_chat"))

app.add_handler(CallbackQueryHandler(profile_edit.edit_name, pattern="edit_name"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_gender, pattern="edit_gender"))
app.add_handler(CallbackQueryHandler(profile_edit.set_gender, pattern="set_gender_"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_age, pattern="edit_age"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_style, pattern="edit_style"))
app.add_handler(CallbackQueryHandler(profile_edit.set_style, pattern="set_style_"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_notifications, pattern="edit_notifications"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_morning, pattern="edit_morning"))
app.add_handler(CallbackQueryHandler(profile_edit.edit_night, pattern="edit_night"))
app.add_handler(CallbackQueryHandler(profile_edit.profile_menu, pattern="profile_menu"))

app.add_handler(CallbackQueryHandler(history.record_mood, pattern="mood_"))
app.add_handler(CallbackQueryHandler(history.full_history, pattern="full_history"))
app.add_handler(CallbackQueryHandler(predictor.predict_tomorrow, pattern="predict_tomorrow"))

# ============================================================
# MessageRouter - فقط زمانی که ConversationHandler فعال نیست
# ============================================================
async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مسیریابی پیام‌ها - فقط زمانی که کاربر در ConversationHandler نیست"""
    logger.info("🔥 message_router فراخوانی شد!")
    
    # اگر ConversationHandler فعال است (ثبت‌نام در حال انجام)، کاری نکن
    if context.user_data.get('conversation_state'):
        logger.info("⏭️ ConversationHandler فعال است، عبور از message_router")
        return
    
    # فقط پیام‌های متنی رو پردازش کن
    if not update.message or not update.message.text:
        logger.info("⏭️ پیام متنی نیست")
        return
    if update.message.text.startswith('/'):
        logger.info("⏭️ پیام کامند است")
        return

    # ============================================================
    # اولویت ۱: حالت ویرایش پروفایل
    # ============================================================
    editing = context.user_data.get('editing')
    if editing == 'name':
        from app.handlers import profile_edit
        await profile_edit.process_name_edit(update, context)
        return
    elif editing == 'age':
        from app.handlers import profile_edit
        await profile_edit.process_age_edit(update, context)
        return

    # ============================================================
    # اولویت ۲: مسیریابی بر اساس current_section
    # ============================================================
    current_section = context.user_data.get('current_section')
    logger.info(f"📩 message_router: current_section={current_section}")

    if current_section == 'past_self':
        if context.user_data.get('past_self_free_chat'):
            await past_self.chat_with_past_self(update, context)
        else:
            await past_self.receive_answer(update, context)
    elif current_section == 'therapist':
        await therapist.chat_with_therapist(update, context)
    else:
        await chat.chat_with_ai(update, context)

app.add_handler(MessageHandler(filters.ALL, message_router))

# ============================================================
# Error Handler
# ============================================================
app.add_error_handler(error_handler)

# ============================================================
# دیتابیس و Scheduler
# ============================================================
logger.info("🔧 در حال اطمینان از وجود جدول‌ها...")
Base.metadata.create_all(engine)
logger.info("✅ جدول‌ها آماده هستند.")

# راه‌اندازی Scheduler با ارسال app برای دسترسی به bot
scheduler = start_scheduler(app)

# ============================================================
# اجرا با Webhook
# ============================================================
if __name__ == "__main__":
    import requests
    
    port = int(os.environ.get("PORT", 10000))
    hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost")
    webhook_url = f"https://{hostname}/{config.BOT_TOKEN}"
    
    try:
        resp = requests.get(f"https://api.telegram.org/bot{config.BOT_TOKEN}/deleteWebhook")
        logger.info(f"✅ Webhook deleted: {resp.json()}")
    except Exception as e:
        logger.warning(f"⚠️ Could not delete webhook: {e}")
    
    logger.info(f"🚀 ربات با Webhook روی پورت {port} راه‌اندازی شد!")
    logger.info(f"🔗 Webhook URL: {webhook_url}")
    
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=config.BOT_TOKEN,
        webhook_url=webhook_url
)
