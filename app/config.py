import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required!")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
    
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
    RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "chatgpt-42.p.rapidapi.com")
    CHAT_API_URL = f"https://{RAPIDAPI_HOST}/conversationgpt4-2"

config = Config()
