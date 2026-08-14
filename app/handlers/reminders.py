from telegram import Update
from telegram.ext import ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from app.database import SessionLocal
from app.models import Reminder

scheduler = AsyncIOScheduler()

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # نمونه ساده - برای کامل کردن به منطق کامل نیاز داره
    await update.message.reply_text("لطفاً زمان (مثلاً 2025-01-01 10:00) و متن رو وارد کن.")
