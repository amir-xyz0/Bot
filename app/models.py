from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, BigInteger, func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    preferred_name = Column(String(100))
    gender = Column(String(20))
    age = Column(Integer)
    chat_style = Column(String(50), default="دوستانه")
    mood_history = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    morning_msg_enabled = Column(Boolean, default=True)
    night_msg_enabled = Column(Boolean, default=True)

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    remind_time = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
