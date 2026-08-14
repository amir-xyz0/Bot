from datetime import datetime, timedelta
import pytz

def get_tehran_time():
    tz = pytz.timezone("Asia/Tehran")
    return datetime.now(tz)

def format_date(date):
    return date.strftime("%Y-%m-%d %H:%M")

def is_premium_valid(user):
    if not user.is_premium:
        return False
    if user.premium_expiry and user.premium_expiry < datetime.now():
        return False
    return True
