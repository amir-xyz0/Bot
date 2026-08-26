import json
import os
import random

# مسیر پوشه data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def load_json_file(filename):
    """بارگذاری فایل JSON از پوشه data"""
    file_path = os.path.join(DATA_DIR, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"⚠️ فایل {filename} پیدا نشد!")
        return None
    except json.JSONDecodeError:
        logger.warning(f"⚠️ فایل {filename} معتبر نیست!")
        return None

def get_morning_message(name='عزیز'):
    """دریافت پیام صبح با نام کاربر"""
    data = load_json_file('morning_messages.json')
    if data and 'text' in data:
        return data['text'].format(name=name)
    return f"🌅 صبح بخیر {name}!"

def get_night_message(name='عزیز'):
    """دریافت پیام شب با نام کاربر"""
    data = load_json_file('night_messages.json')
    if data and 'text' in data:
        return data['text'].format(name=name)
    return f"🌙 شب بخیر {name}!"

def get_random_motivational():
    """دریافت یک پیام انگیزشی رندم"""
    data = load_json_file('motivational_messages.json')
    if data and isinstance(data, list) and len(data) > 0:
        return random.choice(data)
    return "🌟 امروز روز خوبی برات آرزو میکنم!"

def get_random_health_message():
    """دریافت یک پیام سلامتی رندم"""
    try:
        from app.data.health_messages import health_messages
        if health_messages and len(health_messages) > 0:
            return random.choice(health_messages)
    except ImportError:
        pass
    return "🧘 مراقب سلامتیت باش و به خودت برس."

MOOD_REQUEST_MESSAGE = (
    "📝 **ثبت احساسات امروزت:**\n\n"
    "چطور بود امروز؟\n"
    "روزت رو چطور ارزیابی می‌کنی؟"
)
