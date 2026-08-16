from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.database import SessionLocal
from app.models import User

NAME, GENDER, AGE, STYLE = range(4)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # حذف پیام خوش‌آمدگویی (صفحه قبل)
    try:
        await query.message.delete()
    except:
        pass
    # ارسال پیام جدید درخواست اسم
    msg = await query.message.reply_text("📝 **لطفاً نام خود را وارد کنید:**")
    context.user_data['bot_msg_id'] = msg.message_id  # ذخیره ID پیام ربات
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ذخیره نام
    context.user_data["preferred_name"] = update.message.text
    
    # حذف پیام کاربر
    try:
        await update.message.delete()
    except:
        pass
    
    # حذف پیام ربات (سوال قبلی)
    try:
        bot_msg_id = context.user_data.get('bot_msg_id')
        if bot_msg_id:
            await update.message.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=bot_msg_id
            )
    except:
        pass
    
    # ارسال دکمه‌های جنسیت
    keyboard = [
        [InlineKeyboardButton("👨 مرد", callback_data="male")],
        [InlineKeyboardButton("👩 زن", callback_data="female")]
    ]
    msg = await update.message.reply_text(
        "👤 **جنسیت خود را انتخاب کنید:**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data['bot_msg_id'] = msg.message_id
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["gender"] = query.data
    
    # حذف پیام دکمه‌ها (همان پیام ربات)
    try:
        await query.message.delete()
    except:
        pass
    
    # ارسال پیام درخواست سن
    msg = await query.message.reply_text("📅 **سن خود را وارد کنید (عدد):**")
    context.user_data['bot_msg_id'] = msg.message_id
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        if age < 10 or age > 100:
            raise ValueError
        context.user_data["age"] = age
        
        # حذف پیام کاربر
        try:
            await update.message.delete()
        except:
            pass
        
        # حذف پیام ربات (سوال سن)
        try:
            bot_msg_id = context.user_data.get('bot_msg_id')
            if bot_msg_id:
                await update.message.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=bot_msg_id
                )
        except:
            pass
        
        # ارسال دکمه‌های لحن
        keyboard = [
            [InlineKeyboardButton("🤗 دوستانه", callback_data="friendly")],
            [InlineKeyboardButton("👔 رسمی", callback_data="formal")],
            [InlineKeyboardButton("😂 طنز", callback_data="funny")],
            [InlineKeyboardButton("🧘 آرام", callback_data="calm")]
        ]
        msg = await update.message.reply_text(
            "🎭 **لحن مورد نظر خود را انتخاب کنید:**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data['bot_msg_id'] = msg.message_id
        return STYLE
        
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر بین ۱۰ تا ۱۰۰ وارد کنید.")
        return AGE

async def get_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["chat_style"] = query.data
    
    # حذف پیام دکمه‌های لحن
    try:
        await query.message.delete()
    except:
        pass
    
    # ذخیره در دیتابیس
    db = SessionLocal()
    user = User(
        user_id=update.effective_user.id,
        preferred_name=context.user_data["preferred_name"],
        gender=context.user_data["gender"],
        age=context.user_data["age"],
        chat_style=context.user_data["chat_style"]
    )
    db.add(user)
    db.commit()
    db.close()
    
    # ارسال پیام تبریک
    await query.message.reply_text("✅ **ثبت‌نام با موفقیت انجام شد!**")
    
    # ✨ نمایش منوی اصلی به‌عنوان پیام جدید
    from app.handlers.menu import main_menu
    # ایجاد یک Update ساختگی برای فراخوانی main_menu بدون callback
    # اما main_menu برای هر دو حالت (callback یا پیام معمولی) کار میکنه
    # ما یک پیام جدید می‌فرستیم و سپس main_menu رو با همان update صدا می‌زنیم
    # اما main_menu چک میکنه که اگه callback_query نباشه، از update.message استفاده کنه
    # پس ما باید مطمئن بشیم که update.message موجوده – ولی اینجا update از نوع callbackQuery هست.
    # پس بهتره که main_menu رو با یک فراخوانی مستقیم از طریق ارسال پیام جدید صدا بزنیم:
    # یا اینکه خود main_menu رو با تنظیم context و ارسال پیام جدید صدا بزنیم.
    # ساده‌ترین راه: خود main_menu رو به‌عنوان یک تابع معمولی صدا بزنیم که پیام جدید می‌فرسته.
    # اما main_menu با callback هماهنگ شده، پس اگه callback_query نداشته باشه، از update.message استفاده میکنه.
    # برای اینکه کار کنیم، می‌تونیم یک "دستور" جدید شبیه به /menu صادر کنیم.
    # ولی بهترین راه اینه که مستقیم main_menu رو با update فعلی صدا بزنیم، و در main_menu چک کنیم که اگه callback_query نبود، از update.message استفاده کنه.
    # در اینجا update یک callback_query داره، اما ما می‌خواهیم پیام جدیدی بفرستیم که بدون callback باشه.
    # پس بهتره یک پیام جدید با دکمه‌های منو ارسال کنیم.
    
    # راه حل ساده: یک تابع جدا برای ارسال منو به‌عنوان پیام جدید بسازیم:
    from app.handlers.menu import send_main_menu_as_new_message
    # اما برای سادگی، خود main_menu رو با یک ترفند صدا می‌زنیم:
    # ما یک message جدید ایجاد می‌کنیم با استفاده از query.message.reply_text و سپس main_menu رو با اون message صدا می‌زنیم.
    # برای این کار باید main_menu رو بازنویسی کنم تا بتونه پیام ورودی رو بگیره.
    # ولی برای اینکه کار ساده بشه، من main_menu رو طوری می‌نویسم که هم با callback و هم با message کار کنه.
    # الان main_menu این قابلیت رو داره (چک میکنه اگه callback_query باشه، از اون استفاده کنه، در غیر این صورت از update.message).
    # پس کافیه که main_menu رو با update صدا بزنیم. اما update اینجا از نوع callbackQuery هست، پس main_menu از callback استفاده میکنه و پیام رو ویرایش میکنه.
    # اما ما قبلاً پیام دکمه‌ها رو حذف کردیم، پس ویرایش روی Nothing انجام میشه و خطا میده.
    # بهترین راه اینه که main_menu رو به‌صورت زیر صدا بزنیم:
    await main_menu(update, context)
    # ولی مطمئن میشم که main_menu چک کنه که اگه callback_query وجود داره و پیام قبلی حذف شده، به‌جای ویرایش، پیام جدید بفرسته.
    # برای همین main_menu رو بازنویسی می‌کنم تا این حالت رو پوشش بده.
    
    return ConversationHandler.END
