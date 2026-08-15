import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required!")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
    
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
    if not RAPIDAPI_KEY:
        raise ValueError("RAPIDAPI_KEY is required!")
    RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "chatgpt-42.p.rapidapi.com")
    CHAT_API_URL = f"https://{RAPIDAPI_HOST}/conversationgpt4-2"
    
    MORNING_TIME = os.getenv("MORNING_MESSAGE_TIME", "07:00")
    NIGHT_TIME = os.getenv("NIGHT_MESSAGE_TIME", "23:00")

config = Config()
