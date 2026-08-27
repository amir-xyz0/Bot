import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import engine
from datetime import datetime
import json
from sqlalchemy import text as sql_text  # 🔥 تغییر نام برای جلوگیری از تداخل

logger = logging.getLogger(__name__)

async def record_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    mood = query.data.split("_")[1]
    
    logger.info(f"📝 ثبت احساسات: user_id={user_id}, mood={mood}")
    
    mood_map = {
        "good": "😊 خوب",
        "neutral": "😐 معمولی",
        "bad": "😔 بد",
        "happy": "😄 خوشحال",
        "sad": "😢 ناراحت",
        "angry": "😡 عصبانی",
        "tired": "😴 خسته",
        "excited": "🤩 هیجان‌زده",
        "anxious": "😰 مضطرب"
    }
    mood_text = mood_map.get(mood, mood)
    
    try:
        with engine.connect() as connection:
            with connection.begin():
                # ۱. دریافت تاریخچه فعلی
                stmt = sql_text("SELECT mood_history FROM users WHERE user_id = :user_id")
                result = connection.execute(stmt, {"user_id": user_id}).fetchone()
                
                # ۲. تبدیل به لیست
                if result and result[0]:
                    current_history = result[0]
                    if isinstance(current_history, str):
                        try:
                            current_history = json.loads(current_history)
                        except:
                            current_history = []
                    elif not isinstance(current_history, list):
                        current_history = []
                else:
                    current_history = []
                
                # ۳. اضافه کردن احساسات جدید
                new_entry = {
                    "mood": mood,
                    "date": datetime.now().isoformat()
                }
                current_history.append(new_entry)
                
                # ۴. تبدیل به JSON
                history_json = json.dumps(current_history, ensure_ascii=False)
                
                # ۵. ذخیره در دیتابیس
                stmt = sql_text("""
                    UPDATE users 
                    SET mood_history = :history_json 
                    WHERE user_id = :user_id
                """)
                connection.execute(stmt, {
                    "history_json": history_json,
                    "user_id": user_id
                })
        
        logger.info(f"✅ احساسات کاربر {user_id} ذخیره شد. تعداد: {len(current_history)}")
        
        # ۶. حذف پیام دکمه‌های انتخاب احساسات
        try:
            await query.message.delete()
        except:
            pass
        
        # ۷. فقط منوی اصلی رو نمایش بده (بدون پیام موفقیت جداگانه)
        keyboard = [
            [InlineKeyboardButton("💬 گفتگوی همراه", callback_data="chat_menu"),
             InlineKeyboardButton("🧠 مشاوره", callback_data="therapy_menu")],
            [InlineKeyboardButton("🕰️ آیینه‌ی گذشته", callback_data="past_self_menu"),
             InlineKeyboardButton("📊 پیش‌بینی فردا", callback_data="predict_menu")],
            [InlineKeyboardButton("📋 تاریخچه احساسات", callback_data="history_menu"),
             InlineKeyboardButton("👤 پروفایل من", callback_data="profile_menu")]
        ]
        
        await query.message.reply_text(
            "🏠 **خانه**\n\n"
            "به ربات همراه و مشاوره شخصی خود خوش آمدی. 🌸\n\n"
            "اینجا می‌تونی:\n"
            "• با **همراه هوشمند** خودت گفتگو کنی\n"
            "• از **مشاوره‌های عمیق** بهره‌مند بشی\n"
            "• با **گذشته‌ات** ارتباط بگیری و ازش یاد بگیری\n"
            "• احساساتت رو **ثبت** کنی و روندش رو ببینی\n"
            "• و خیلی چیزهای دیگه...\n\n"
            "✨ هر روزت بهتر از دیروز ❤️",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"❌ خطا در ثبت احساسات: {e}")
        await query.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کن.")

async def full_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"📋 نمایش تاریخچه: user_id={user_id}")
    
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        message = query.message
    else:
        message = update.message
    
    if not message:
        return
    
    try:
        with engine.connect() as connection:
            stmt = sql_text("SELECT mood_history FROM users WHERE user_id = :user_id")
            result = connection.execute(stmt, {"user_id": user_id}).fetchone()
        
        if not result:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            await message.reply_text(
                "❗ کاربر یافت نشد.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # تبدیل به لیست
        mood_history = result[0]
        if mood_history is None:
            mood_history = []
        elif isinstance(mood_history, str):
            try:
                mood_history = json.loads(mood_history)
            except:
                mood_history = []
        elif not isinstance(mood_history, list):
            mood_history = []
        
        logger.info(f"📊 تعداد احساسات ثبت‌شده: {len(mood_history)}")
        
        if not mood_history or len(mood_history) == 0:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            await message.reply_text(
                "📭 **تاریخچه‌ای وجود ندارد.**\n\n"
                "هنوز احساساتی ثبت نکردی.\n"
                "از منوی اصلی می‌تونی احساساتت رو ثبت کنی.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # نمایش ۳۰ مورد آخر
        history = mood_history[-30:]
        result_text = "📋 **تاریخچه احساسات شما:**\n\n"  # 🔥 تغییر نام به result_text
        mood_emoji = {
            "good": "😊",
            "happy": "😄",
            "neutral": "😐",
            "bad": "😔",
            "sad": "😢",
            "angry": "😡",
            "excited": "🤩",
            "tired": "😴",
            "anxious": "😰"
        }
        
        for item in reversed(history):
            mood = item.get("mood", "نامشخص")
            date = item.get("date", "")
            if date:
                try:
                    dt = datetime.fromisoformat(date)
                    date_str = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    date_str = date
            else:
                date_str = "نامشخص"
            
            emoji = mood_emoji.get(mood, "🤔")
            result_text += f"{emoji} **{mood}** - {date_str}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"❌ خطا در نمایش تاریخچه: {e}")
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کن.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
