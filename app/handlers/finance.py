from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.models import User, Transaction
from app.utils.helpers import is_premium_valid
from datetime import datetime, timedelta

async def add_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    db.close()
    
    if not user:
        await update.message.reply_text("❌ اول /start رو بزن!")
        return
    
    if not is_premium_valid(user):
        keyboard = [[InlineKeyboardButton("💎 تبدیل به پریمیوم", callback_data="buy_premium")]]
        await update.message.reply_text(
            "🔒 این بخش فقط برای کاربران پریمیوم فعاله!\n"
            "با خرید اشتراک پریمیوم به همه‌ی امکانات دسترسی پیدا کن.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    try:
        parts = update.message.text.split("|")
        amount = float(parts[0].strip())
        category = parts[1].strip() if len(parts) > 1 else "سایر"
        description = parts[2].strip() if len(parts) > 2 else ""
        
        db = SessionLocal()
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            category=category,
            description=description
        )
        db.add(transaction)
        db.commit()
        db.close()
        
        await update.message.reply_text(
            f"✅ تراکنش ثبت شد!\n"
            f"💰 مبلغ: {amount:,} تومان\n"
            f"📂 دسته‌بندی: {category}\n"
            f"📝 توضیحات: {description}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}\nفرمت صحیح: `100000 | خوراک | ناهار`")

async def show_finance_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter_by(user_id=user_id).first()
    transactions = db.query(Transaction).filter_by(user_id=user_id).all()
    db.close()
    
    if not is_premium_valid(user):
        keyboard = [[InlineKeyboardButton("💎 تبدیل به پریمیوم", callback_data="buy_premium")]]
        await update.message.reply_text(
            "🔒 این بخش فقط برای کاربران پریمیوم فعاله!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    if not transactions:
        await update.message.reply_text("📭 هیچ تراکنشی ثبت نشده!")
        return
    
    total = sum(t.amount for t in transactions)
    this_month = sum(t.amount for t in transactions if t.date > datetime.now() - timedelta(days=30))
    
    categories = {}
    for t in transactions:
        if t.date > datetime.now() - timedelta(days=30):
            categories[t.category] = categories.get(t.category, 0) + t.amount
    
    text = "💰 **گزارش مالی ماهانه**\n\n"
    text += f"کل هزینه‌ها: {total:,} تومان\n"
    text += f"هزینه‌ی این ماه: {this_month:,} تومان\n\n"
    text += "**دسته‌بندی‌ها:**\n"
    for cat, amt in categories.items():
        text += f"• {cat}: {amt:,} تومان\n"
    
    keyboard = [[InlineKeyboardButton("📥 خروجی CSV", callback_data="export_finance")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # منطق خرید پریمیوم - می‌تونه با Zarinpal یا هر درگاه دیگه باشه
    await query.edit_message_text(
        "💎 **خرید اشتراک پریمیوم**\n\n"
        "هزینه: ۷۰,۰۰۰ تومان / ماه\n\n"
        "مزایا:\n"
        "✅ مدیریت مالی پیشرفته\n"
        "✅ ذخیره‌سازی نامحدود\n"
        "✅ چت نامحدود با هوش مصنوعی\n"
        "✅ تحلیل پیشرفته‌ی احساسات\n\n"
        "لطفاً مبلغ رو به شماره کارت ... واریز کن.\n"
        "بعد از واریز، رسید رو بفرست تا فعال بشه."
    )
