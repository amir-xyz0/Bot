from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import config

engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,          # بررسی سلامت اتصال قبل از استفاده
    pool_recycle=3600,           # بازیابی اتصالات بعد از ۱ ساعت
    pool_size=5,                 # حداکثر ۵ اتصال همزمان
    max_overflow=10,             # حداکثر ۱۰ اتصال اضافی
    echo_pool=False,             # لاگ‌های پول رو خاموش کن (برای کاهش خطاها)
    pool_reset_on_return="commit" # ریست اتصال فقط در زمان commit
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
