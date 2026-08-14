import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

WORDS = ["کامپیوتر", "تلگرام", "ربات", "کتاب", "مدرسه", "دوستی", "زندگی", "خورشید", "ماه", "ستاره"]
GAME_STATES = {}

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = random.choice(WORDS)
    GAME_STATES[update.effective_user.id] = {
        "word": word,
        "guesses": [],
        "attempts": 6,
        "hint": word[0] + "_" * (len(word) - 1)
    }
    
    keyboard = [
        [InlineKeyboardButton("🔤 حدس حرف", callback_data="guess_letter")],
        [InlineKeyboardButton("💡 راهنما", callback_data="game_hint")],
        [InlineKeyboardButton("🚪 خروج", callback_data="game_exit")]
    ]
    
    await update.message.reply_text(
        f"🎮 **بازی حدس کلمه**\n\n"
        f"یک کلمه {len(word)} حرفی رو حدس بزن!\n"
        f"📌 کلمه: {GAME_STATES[update.effective_user.id]['hint']}\n"
        f"❤️ شانس باقی‌مونده: {GAME_STATES[update.effective_user.id]['attempts']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def game_guess_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔤 یه حرف (فارسی) رو وارد کن:")

async def process_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in GAME_STATES:
        await update.message.reply_text("❌ ابتدا /game رو بزن!")
        return
    
    state = GAME_STATES[user_id]
    letter = update.message.text.strip()
    
    if len(letter) != 1 or not letter.isalpha():
        await update.message.reply_text("❌ فقط یه حرف فارسی وارد کن!")
        return
    
    if letter in state["guesses"]:
        await update.message.reply_text("⏳ این حرف رو قبلاً حدس زدی!")
        return
    
    state["guesses"].append(letter)
    
    if letter in state["word"]:
        # حرف درست
        hint = ""
        for c in state["word"]:
            if c in state["guesses"]:
                hint += c
            else:
                hint += "_"
        state["hint"] = hint
        
        if "_" not in hint:
            await update.message.reply_text(f"🎉 آفرین! کلمه رو پیدا کردی: {state['word']}\nامتیازت ثبت شد!")
            del GAME_STATES[user_id]
            return
    else:
        # حرف اشتباه
        state["attempts"] -= 1
        if state["attempts"] <= 0:
            await update.message.reply_text(f"💔 باختی! کلمه درست: {state['word']}\nدفعه بعد حتماً می‌بری!")
            del GAME_STATES[user_id]
            return
    
    keyboard = [
        [InlineKeyboardButton("🔤 حدس حرف", callback_data="guess_letter")],
        [InlineKeyboardButton("💡 راهنما", callback_data="game_hint")],
        [InlineKeyboardButton("🚪 خروج", callback_data="game_exit")]
    ]
    
    await update.message.reply_text(
        f"🎮 **ادامه بازی**\n\n"
        f"📌 کلمه: {state['hint']}\n"
        f"❤️ شانس باقی‌مونده: {state['attempts']}\n"
        f"🔤 حروف حدس‌زده: {', '.join(state['guesses'])}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def game_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    if user_id not in GAME_STATES:
        await query.edit_message_text("❌ بازی فعالی وجود نداره! /game رو بزن.")
        return
    
    state = GAME_STATES[user_id]
    hint_word = state["word"]
    hint = hint_word[0] + "_" * (len(hint_word) - 1)
    await query.edit_message_text(f"💡 راهنما: کلمه {len(hint_word)} حرفیه و با «{hint_word[0]}» شروع میشه.")

async def game_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if user_id in GAME_STATES:
        del GAME_STATES[user_id]
    await query.edit_message_text("🚪 از بازی خارج شدی. هر وقت خواستی /game رو بزن!")
