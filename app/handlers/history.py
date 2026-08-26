import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User
from datetime import datetime
import json

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
        "happy": "😄 خوشحال",
        "sad": "😢 ناراحت",
        "angry": "😡 عصبانی",
        "tired": "😴 خسته",
        "excited": "🤩 هیجان‌زده",
        "anxious": "😰 مضطرب"
    }
    mood_text = mood_map.get(mood, mood)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            await query.message.reply_text("❗ کاربر یافت نشد.")
            db.close()
            return
        
        # 🔥 روش اصولی برای کار با JSON در PostgreSQL
        # اگر mood_history None هست، یک لیست خالی بساز
        if user.mood_history is None:
            user.mood_history = []
            logger.info("📝 mood_history جدید (لیست خالی) ایجاد شد.")
        
        # 🔥 اطمینان از اینکه mood_history یک لیست هست
        current_history = user.mood_history
        if not isinstance(current_history, list):
            try:
                # اگر string هست، به لیست تبدیل کن
                if isinstance(current_history, str):
                    current_history = json.loads(current_history)
                else:
                    current_history = []
            except:
                current_history = []
            logger.warning(f"⚠️ mood_history به لیست تبدیل شد. نوع قبلی: {type(user.mood_history)}")
        
        # اضافه کردن احساسات جدید
        new_entry = {
            "mood": mood,
            "date": datetime.now().isoformat()
        }
        current_history.append(new_entry)
        
        # 🔥 ذخیره در دیتابیس
        user.mood_history = current_history
        db.commit()
        
        # 🔥 برای اطمینان، دوباره از دیتابیس بخون
        db.refresh(user)
        
        logger.info(f"✅ احساسات کاربر {user_id} ذخیره شد. تعداد کل: {len(user.mood_history)}")
        logger.info(f"📋 محتوای mood_history: {user.mood_history}")
        
        # حذف پیام دکمه‌های انتخاب احساسات
        try:
            await query.message.delete()
            logger.info("✅ پیام دکمه‌های احساسات حذف شد.")
        except Exception as e:
            logger.warning(f"⚠️ خطا در حذف پیام: {e}")
        
        # 🔥 ارسال مستقیم منوی اصلی (بدون پیام تأیید جداگانه)
        keyboard = [
            [InlineKeyboardButton("💬 گفتگوی همراه", callback_data="chat_menu"),
             InlineKeyboardButton("🧠 مشاوره", callback_data="therapy_menu")],
            [InlineKeyboardButton("🕰️ آیینه‌ی گذشته", callback_data="past_self_menu"),
             InlineKeyboardButton("📊 پیش‌بینی فردا", callback_data="predict_menu")],
            [InlineKeyboardButton("📋 تاریخچه احساسات", callback_data="history_menu"),
             InlineKeyboardButton("👤 پروفایل من", callback_data="profile_menu")]
        ]
        
        text = (
            "🏠 **خانه**\n\n"
            f"✅ احساسات امروزت (**{mood_text}**) با موفقیت ثبت شد! 🌸\n\n"
            "به ربات همراه و مشاوره شخصی خود خوش آمدی.\n\n"
            "اینجا می‌تونی:\n"
            "• با **همراه هوشمند** خودت گفتگو کنی\n"
            "• از **مشاوره‌های عمیق** بهره‌مند بشی\n"
            "• با **گذشته‌ات** ارتباط بگیری و ازش یاد بگیری\n"
            "• احساساتت رو **ثبت** کنی و روندش رو ببینی\n"
            "• و خیلی چیزهای دیگه...\n\n"
            "✨ هر روزت بهتر از دیروز ❤️"
        )
        
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        logger.error(f"❌ خطا در ثبت احساسات: {e}")
        db.rollback()
        await query.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کن.")
    finally:
        db.close()

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
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            await message.reply_text(
                "❗ کاربر یافت نشد.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            db.close()
            return
        
        # 🔥 دریافت و تبدیل mood_history
        mood_history = user.mood_history
        if mood_history is None:
            mood_history = []
        elif not isinstance(mood_history, list):
            try:
                if isinstance(mood_history, str):
                    mood_history = json.loads(mood_history)
                else:
                    mood_history = []
            except:
                mood_history = []
        
        if not mood_history or len(mood_history) == 0:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
            text = (
                "📭 **تاریخچه‌ای وجود ندارد.**\n\n"
                "هنوز احساساتی ثبت نکردی.\n"
                "از منوی اصلی می‌تونی احساساتت رو ثبت کنی."
            )
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            db.close()
            return
        
        logger.info(f"📊 تعداد احساسات ثبت‌شده: {len(mood_history)}")
        
        history = mood_history[-30:]
        text = "📋 **تاریخچه احساسات شما:**\n\n"
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
            text += f"{emoji} **{mood}** - {date_str}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"❌ خطا در نمایش تاریخچه: {e}")
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="main_menu")]]
        await message.reply_text(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کن.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        db.close()
