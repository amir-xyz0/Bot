from app.database import engine, SessionLocal
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # چک کردن وجود ستون personality_profile
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='personality_profile'
        """))
        if not result.fetchone():
            db.execute(text("ALTER TABLE users ADD COLUMN personality_profile JSON;"))
            db.commit()
            print("✅ ستون personality_profile اضافه شد!")
        else:
            print("✅ ستون personality_profile قبلاً وجود دارد.")
    except Exception as e:
        print(f"❌ خطا: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
