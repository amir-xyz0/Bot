from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base
import os

# تشخیص نوع دیتابیس
DATABASE_URL = os.getenv("DATABASE_URL", "")
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    preferred_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    chat_style = Column(String, default="friendly")
    notifications = Column(Boolean, default=True)
    morning_msg_enabled = Column(Boolean, default=True)
    night_msg_enabled = Column(Boolean, default=True)
    personality_profile = Column(JSONB if IS_POSTGRES else JSON, nullable=True)
    mood_history = Column(JSONB if IS_POSTGRES else JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
