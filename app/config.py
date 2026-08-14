import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required!")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MORNING_TIME = os.getenv("MORNING_MESSAGE_TIME", "07:00")
    NIGHT_TIME = os.getenv("NIGHT_MESSAGE_TIME", "23:00")
    
    # تنظیمات OpenAI
    OPENAI_MODEL = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS = 150

config = Config()
