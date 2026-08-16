import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required!")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
    
    # ===== RapidAPI Vision (جایگزین ChatGPT) =====
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
    RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "chatgpt-vision1.p.rapidapi.com")
    CHAT_API_URL = f"https://{RAPIDAPI_HOST}/matagvision2"
    
    # ===== Gemini API (گزینه دوم) =====
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

config = Config()
