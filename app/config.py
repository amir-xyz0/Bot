import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required!")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
    
    # ===== GapGPT (اولویت اول) =====
    GAPGPT_API_KEY = os.getenv("GAPGPT_API_KEY")
    GAPGPT_BASE_URL = os.getenv("GAPGPT_BASE_URL", "https://api.gapgpt.app/v1")
    GAPGPT_MODEL = os.getenv("GAPGPT_MODEL", "gpt-4o")
    
    # ===== RapidAPI Vision (اولویت دوم) =====
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
    RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "chatgpt-vision1.p.rapidapi.com")
    CHAT_API_URL = f"https://{RAPIDAPI_HOST}/matagvision2"

config = Config()
