from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import config
import os

# تعیین نوع دیتابیس بر اساس URL
database_url = config.DATABASE_URL

# اگر از PostgreSQL استفاده می‌کنی، پارامترهای اضافی رو حذف کن
if database_url and database_url.startswith("postgresql"):
    # برای PostgreSQL، هیچ connect_args ای ارسال نکن
    engine = create_engine(database_url)
else:
    # برای SQLite (و سایر موارد)
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
