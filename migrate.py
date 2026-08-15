from app.database import engine, SessionLocal
from app.models import User
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # اضافه کردن ستون last_activity
        db.execute(text("ALTER TABLE users ADD COLUMN last_activity TIMESTAMP WITH TIME ZONE;"))
        db.commit()
        print("✅ ستون last_activity اضافه شد!")
        
        # به‌روزرسانی last_activity برای کاربران موجود
        db.execute(text("UPDATE users SET last_activity = created_at WHERE last_activity IS NULL;"))
        db.commit()
        print("✅ last_activity برای کاربران موجود به‌روزرسانی شد!")
        
        # اضافه کردن ستون is_premium (اگه وجود نداره)
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT FALSE;"))
            db.commit()
            print("✅ ستون is_premium اضافه شد!")
        except Exception:
            print("⚠️ ستون is_premium قبلاً وجود داشت.")
        
        # اضافه کردن ستون premium_expiry
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN premium_expiry TIMESTAMP WITH TIME ZONE;"))
            db.commit()
            print("✅ ستون premium_expiry اضافه شد!")
        except Exception:
            print("⚠️ ستون premium_expiry قبلاً وجود داشت.")
        
        # اضافه کردن ستون morning_msg_enabled
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN morning_msg_enabled BOOLEAN DEFAULT TRUE;"))
            db.commit()
            print("✅ ستون morning_msg_enabled اضافه شد!")
        except Exception:
            print("⚠️ ستون morning_msg_enabled قبلاً وجود داشت.")
        
        # اضافه کردن ستون night_msg_enabled
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN night_msg_enabled BOOLEAN DEFAULT TRUE;"))
            db.commit()
            print("✅ ستون night_msg_enabled اضافه شد!")
        except Exception:
            print("⚠️ ستون night_msg_enabled قبلاً وجود داشت.")
            
        print("🎉 مهاجرت با موفقیت انجام شد!")
        
    except Exception as e:
        print(f"❌ خطا: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
