#!/usr/bin/env python3
import logging
import os
import sys
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# ====== ۱. سرور کوچک برای Health Check ======
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# ====== ۲. اجرای سرور Health Check در پس‌زمینه ======
threading.Thread(target=run_health_server, daemon=True).start()

# ====== ۳. بقیه کدهای ربات (دقیقاً مثل قبل) ======
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        CallbackQueryHandler,
        MessageHandler,
        filters,
        ContextTypes
    )
except Exception as e:
    logger.error(f"❌ خطا در ایمپورت telegram: {e}")
    sys.exit(1)

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models import User

ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))

if not ADMIN_BOT_TOKEN:
    logger.error("❌ ADMIN_BOT_TOKEN تنظیم نشده!")
    sys.exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ITEMS_PER_PAGE = 5

# ====== ۴. هندلرهای ربات (دقیقاً مثل قبل) ======
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="⚠️ خطا:", exc_info=context.error)
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("❌ خطایی رخ داد.")
        except:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ شما دسترسی به این ربات ندارید.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 آمار کاربران", callback_data="stats")],
        [InlineKeyboardButton("📋 لیست کامل کاربران", callback_data="all_users")],
        [InlineKeyboardButton("📨 ارسال پیام عمومی", callback_data="broadcast")],
        [InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="search_user")]
    ]
    await update.message.reply_text(
        "🤖 **پنل مدیریت**\n\n"
        "سلام ادمین عزیز! 👋\n"
        "از اینجا ربات رو مدیریت کن.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"⚠️ خطا در answer: {e}")
        return
    
    if update.effective_user.id != ADMIN_USER_ID:
        await query.edit_message_text("⛔ دسترسی ندارید.")
        return
    
    db = SessionLocal()
    try:
        total = db.query(User).count()
        week_ago = datetime.now() - timedelta(days=7)
        active = 0
        users = db.query(User).all()
        for user in users:
            if user.mood_history:
                try:
                    last_mood = user.mood_history[-1]
                    if last_mood.get('date'):
                        mood_date = datetime.fromisoformat(last_mood['date'])
                        if mood_date > week_ago:
                            active += 1
                except:
                    pass
        
        text = (
            f"📊 **آمار کاربران**\n\n"
            f"👥 کل کاربران: {total}\n"
            f"✅ فعال‌های هفته اخیر: {active}\n"
            f"📅 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
        )
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await query.edit_message_text(f"❌ خطا: {e}")
    finally:
        db.close()

async def all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"⚠️ خطا در answer: {e}")
        return
    
    if update.effective_user.id != ADMIN_USER_ID:
        await query.edit_message_text("⛔ دسترسی ندارید.")
        return
    context.user_data['user_list_page'] = 0
    await show_users_page(update, context)

async def show_users_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = context.user_data.get('user_list_page', 0)
    db = SessionLocal()
    try:
        total_users = db.query(User).count()
        total_pages = (total_users + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        if page >= total_pages:
            page = total_pages - 1
        if page < 0:
            page = 0
        context.user_data['user_list_page'] = page
        
        users = db.query(User).order_by(User.created_at.desc()).offset(page * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()
        
        if not users:
            await query.edit_message_text("📭 کاربری ثبت‌نام نکرده.")
            return
        
        text = f"📋 **لیست کاربران (صفحه {page+1} از {total_pages}):**\n\n"
        for i, user in enumerate(users, 1):
            created = user.created_at.strftime('%Y/%m/%d') if user.created_at else 'نامشخص'
            moods = len(user.mood_history) if user.mood_history else 0
            text += (
                f"{i + (page * ITEMS_PER_PAGE)}. 👤 {user.preferred_name}\n"
                f"   🆔 {user.user_id}\n"
                f"   📅 {created} | 🎭 {user.chat_style}\n"
                f"   📊 {moods} احساسات ثبت شده\n"
                f"   {'─' * 15}\n"
            )
        
        keyboard = []
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data="users_prev"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data="users_next"))
        if nav_buttons:
            keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back")])
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
        await query.edit_message_text(f"❌ خطا: {e}")
    finally:
        db.close()

async def users_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"⚠️ خطا در answer: {e}")
        return
    page = context.user_data.get('user_list_page', 0)
    context.user_data['user_list_page'] = page + 1
    await show_users_page(update, context)

async def users_prev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"⚠️ خطا در answer: {e}")
        return
    page = context.user_data.get('user_list_page', 0)
    context.user_data['user_list_page'] = page - 1
    await show_users_page(update, context)

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"⚠️ خطا در answer: {e}")
        return
    
    if update.effective_user.id != ADMIN_USER_ID:
        await query.edit_message_text("⛔ دسترسی ندارید.")
        return
    context.user_data['broadcast_mode'] = True
    keyboard = [[InlineKeyboardButton("🔙 لغو", callback_data="back")]]
    await query.edit_message_text(
        "📨 **ارسال پیام عمومی**\n\n"
        "پیام خود را بنویسید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('broadcast_mode'):
        return
    if update.effective_user.id != ADMIN_USER_ID:
        return
    
    message_text = update.message.text
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            await update.message.reply_text("📭 هیچ کاربری ثبت‌نام نکرده.")
            return
        
        await update.message.reply_text(f"⏳ ارسال به {len(users)} کاربر...")
        success, fail = 0, 0
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.user_id,
                    text=f"📢 **پیام از ادمین:**\n\n{message_text}"
                )
                success += 1
            except:
                fail += 1
        
        context.user_data['broadcast_mode'] = False
        keyboard = [[InlineKeyboardButton("🔙 پنل", callback_data="back")]]
        await update.message.reply_text(
            f"✅ **نتیجه:**\nموفق: {success}\nناموفق: {fail}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")
    finally:
        db.close()

async def search_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"⚠️ خطا در answer: {e}")
        return
    
    if update.effective_user.id != ADMIN_USER_ID:
        await query.edit_message_text("⛔ دسترسی ندارید.")
        return
    context.user_data['search_mode'] = True
    keyboard = [[InlineKeyboardButton("🔙 لغو", callback_data="back")]]
    await query.edit_message_text(
        "🔍 **جستجوی کاربر**\n\n"
        "نام یا آیدی عددی را وارد کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('search_mode'):
        return
    if update.effective_user.id != ADMIN_USER_ID:
        return
    
    search = update.message.text.strip()
    db = SessionLocal()
    try:
        if search.isdigit():
            user = db.query(User).filter_by(user_id=int(search)).first()
            users = [user] if user else []
        else:
            users = db.query(User).filter(User.preferred_name.ilike(f"%{search}%")).all()
        
        if not users:
            await update.message.reply_text("🔍 پیدا نشد.")
            context.user_data['search_mode'] = False
            return
        
        text = "🔍 **نتیجه:**\n\n"
        for user in users[:5]:
            created = user.created_at.strftime('%Y/%m/%d') if user.created_at else 'نامشخص'
            text += f"👤 {user.preferred_name}\n🆔 {user.user_id}\n📅 {created}\n{'─'*20}\n"
        
        context.user_data['search_mode'] = False
        keyboard = [[InlineKeyboardButton("🔙 پنل", callback_data="back")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")
    finally:
        db.close()

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"⚠️ خطا در answer: {e}")
        return
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("📋 لیست کامل کاربران", callback_data="all_users")],
        [InlineKeyboardButton("📨 ارسال پیام عمومی", callback_data="broadcast")],
        [InlineKeyboardButton("🔍 جستجو", callback_data="search_user")]
    ]
    await query.edit_message_text(
        "🤖 **پنل مدیریت**\n\n"
        "انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====== ۵. اجرای اصلی ربات ======
def main():
    try:
        application = Application.builder().token(ADMIN_BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(stats, pattern="stats"))
        application.add_handler(CallbackQueryHandler(all_users, pattern="all_users"))
        application.add_handler(CallbackQueryHandler(users_next, pattern="users_next"))
        application.add_handler(CallbackQueryHandler(users_prev, pattern="users_prev"))
        application.add_handler(CallbackQueryHandler(broadcast_start, pattern="broadcast"))
        application.add_handler(CallbackQueryHandler(search_user_start, pattern="search_user"))
        application.add_handler(CallbackQueryHandler(back, pattern="back"))
        
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search))
        
        application.add_error_handler(error_handler)
        
        logger.info("🚀 ربات ادمین و سرور Health Check راه‌اندازی شد!")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی: {e}")
        raise

if __name__ == "__main__":
    main()
