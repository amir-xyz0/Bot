from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, BigInteger, func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    preferred_name = Column(String(100))
    gender = Column(String(20))
    age = Column(Integer)
    chat_style = Column(String(50), default="friendly")
    mood_history = Column(JSON, default=list)
    personality_profile = Column(JSON, default=None)  # جدید: برای خود گذشته
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    morning_msg_enabled = Column(Boolean, default=True)
    night_msg_enabled = Column(Boolean, default=True)
    health_msg_enabled = Column(Boolean, default=True)
    sent_health_messages = Column(JSON, default=list)
