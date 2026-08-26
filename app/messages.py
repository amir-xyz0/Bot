import json
import os
import random
import logging
from typing import List

logger = logging.getLogger(__name__)

# مسیر پوشه data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# ============================================================
# کلاس مدیریت پیام‌های چرخشی (بدون تکرار)
# ============================================================
class CircularMessageManager:
    """مدیریت پیام‌ها به صورت چرخشی بدون تکرار"""
    
    def __init__(self, messages: List[str]):
        self.messages = messages.copy()
        self.index = 0
        self._shuffle()
    
    def _shuffle(self):
        """خلوط کردن پیام‌ها"""
        if self.messages:
            random.shuffle(self.messages)
            self.index = 0
    
    def get_next(self) -> str:
        """دریافت پیام بعدی (چرخشی)"""
        if not self.messages:
            return None
        
        if self.index >= len(self.messages):
            self._shuffle()
        
        msg = self.messages[self.index]
        self.index += 1
        return msg
    
    def add_messages(self, new_messages: List[str]):
        """اضافه کردن پیام‌های جدید به لیست"""
        self.messages.extend(new_messages)
        self._shuffle()
    
    def count(self) -> int:
        """تعداد پیام‌های موجود"""
        return len(self.messages)

# ============================================================
# بارگذاری دیتاها از فایل‌های JSON
# ============================================================
def load_json_file(filename):
    """بارگذاری فایل JSON از پوشه data"""
    file_path = os.path.join(DATA_DIR, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"⚠️ فایل {filename} پیدا نشد! از مقدار پیش‌فرض استفاده می‌شود.")
        return None
    except json.JSONDecodeError:
        logger.warning(f"⚠️ فایل {filename} معتبر نیست!")
        return None

# ============================================================
# بارگذاری پیام‌های انگیزشی
# ============================================================
_motivational_messages = None
_motivational_manager = None

def get_motivational_messages():
    """بارگذاری پیام‌های انگیزشی از فایل JSON"""
    global _motivational_messages, _motivational_manager
    
    if _motivational_messages is None:
        data = load_json_file('motivational_messages.json')
        if data and isinstance(data, list) and len(data) > 0:
            _motivational_messages = data
        else:
            # پیام‌های پیش‌فرض (در صورت نبود فایل)
            _motivational_messages = [
                "💪 **یه یادآوری کوچیک:**\n\nامروز قراره اتفاقای خوبی بیوفته. فقط کافیه بهش ایمان داشته باشی.",
                "🌟 **به خودت ایمان داشته باش:**\n\nتو از چیزی که فکر می‌کنی قوی‌تری.",
                "🌸 **امروز روز توئه:**\n\nلبخند بزن، چون ارزشش رو داری."
            ]
        
        _motivational_manager = CircularMessageManager(_motivational_messages)
        logger.info(f"✅ {len(_motivational_messages)} پیام انگیزشی بارگذاری شد.")
    
    return _motivational_messages, _motivational_manager

def get_random_motivational():
    """دریافت یک پیام انگیزشی بدون تکرار (چرخشی)"""
    _, manager = get_motivational_messages()
    return manager.get_next()

# ============================================================
# بارگذاری پیام‌های سلامتی
# ============================================================
_health_messages = None
_health_manager = None

def get_health_messages():
    """بارگذاری پیام‌های سلامتی"""
    global _health_messages, _health_manager
    
    if _health_messages is None:
        # تلاش برای بارگذاری از فایل health_messages.py
        try:
            from app.data.health_messages import health_messages as health_list
            if health_list and len(health_list) > 0:
                _health_messages = health_list
            else:
                raise ImportError
        except (ImportError, AttributeError):
            # تلاش برای بارگذاری از فایل JSON
            data = load_json_file('health_messages.json')
            if data and isinstance(data, list) and len(data) > 0:
                _health_messages = data
            else:
                # پیام‌های پیش‌فرض
                _health_messages = [
                    "🧘 **مراقب سلامتیت باش:**\n\nهر روز چند دقیقه نفس عمیق بکش و به بدنت استراحت بده.",
                    "🥗 **تغذیه سالم:**\n\nامروز یه غذای سالم و مقوی بخور. بدنت به انرژی خوب نیاز داره.",
                    "🚶‍♂️ **فعالیت بدنی:**\n\nتنها ۱۵ دقیقه پیاده‌روی می‌تونه حالت رو بهتر کنه."
                ]
        
        _health_manager = CircularMessageManager(_health_messages)
        logger.info(f"✅ {len(_health_messages)} پیام سلامتی بارگذاری شد.")
    
    return _health_messages, _health_manager

def get_random_health_message():
    """دریافت یک پیام سلامتی بدون تکرار (چرخشی)"""
    _, manager = get_health_messages()
    return manager.get_next()

# ============================================================
# پیام‌های ثابت صبح و شب
# ============================================================
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

# ============================================================
# پیام‌های ثابت مربوط به احساسات
# ============================================================
MOOD_REQUEST_MESSAGE = (
    "📝 **ثبت احساسات امروزت:**\n\n"
    "چطور بود امروز؟\n"
    "روزت رو چطور ارزیابی می‌کنی؟"
)

MOOD_THANK_MESSAGE = (
    "✅ احساسات شما با موفقیت ثبت شد! 🌸\n\n"
    "حالت امروزت: {}"
)
