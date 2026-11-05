import random
from datetime import datetime, timedelta
from sqlmodel import Session, select
from models.user import User

def generate_otp(length=4):
    """Generate a random OTP"""
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    print(f" Generated OTP: {otp}")
    return otp

def store_otp_in_db(mobile_no: str, otp: str, db: Session):
    """Store OTP in user record"""
    try:
        user = db.exec(select(User).where(User.mobile_no == mobile_no)).first()
        if user:
            user.otp_code = otp
            user.otp_created_at = datetime.utcnow()
            user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
            db.add(user)
            db.commit()
            print(f" OTP stored for {mobile_no}: {otp}")
            return True
        else:
            print(f" User not found for mobile: {mobile_no}")
            return False
    except Exception as e:
        print(f" Error storing OTP: {e}")
        return False

def verify_otp_in_db(mobile_no: str, otp: str, db: Session):
    """Verify OTP from database"""
    try:
        user = db.exec(select(User).where(User.mobile_no == mobile_no)).first()
        if not user:
            print(f" User not found for mobile: {mobile_no}")
            return False
        
        print(f" Checking OTP for {mobile_no}:")
        print(f"   Stored OTP: {user.otp_code}")
        print(f"   Provided OTP: {otp}")
        print(f"   OTP Expires At: {user.otp_expires_at}")
        
        # Check if OTP exists and is not expired
        if (user.otp_code and 
            user.otp_code == otp and 
            user.otp_expires_at and 
            user.otp_expires_at > datetime.utcnow()):
            print(f" OTP verified successfully for {mobile_no}")
            return True
        
        print(f" OTP verification failed for {mobile_no}")
        return False
        
    except Exception as e:
        print(f" Error verifying OTP: {e}")
        return False

def clear_otp_from_db(mobile_no: str, db: Session):
    """Clear OTP after verification"""
    try:
        user = db.exec(select(User).where(User.mobile_no == mobile_no)).first()
        if user:
            user.otp_code = None
            user.otp_created_at = None
            user.otp_expires_at = None
            db.add(user)
            db.commit()
            print(f" OTP cleared for {mobile_no}")
            return True
        return False
    except Exception as e:
        print(f" Error clearing OTP: {e}")
        return False

def send_otp_via_sms(mobile_no: str, otp: str):
    """Mock SMS function"""
    print(f" SMS OTP for {mobile_no}: {otp}")
    print(f" Your OTP is: {otp}")
    return True