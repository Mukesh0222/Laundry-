import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

def generate_otp():
    """Generate numeric OTP."""
    return str(random.randint(1000, 9999))

def store_otp_in_db(mobile_no: str, otp: str, db: Session):
    """Store OTP in user table itself."""
    from models import User
    
    # Find user by mobile number
    user = db.query(User).filter(User.mobile_no == mobile_no).first()
    if not user:
        raise ValueError("User not found")
    
    # Store OTP in user record
    user.otp_code = otp
    user.otp_created_at = datetime.now()
    user.otp_expires_at = datetime.now() + timedelta(minutes=5)  # 5 minutes expiry
    
    db.commit()
    db.refresh(user)

def verify_otp_in_db(mobile_no: str, otp: str, db: Session) -> bool:
    """Verify OTP from user table."""
    from models import User
    
    user = db.query(User).filter(
        User.mobile_no == mobile_no,
        User.otp_code == otp,
        User.otp_expires_at >= datetime.now()
    ).first()
    
    return user is not None

def send_otp_via_sms(mobile_no: str, otp: str):
    """Send OTP via SMS service."""
    print(f"Sending OTP {otp} to {mobile_no}")
    # TODO: Integrate with your SMS gateway

def clear_otp_from_db(mobile_no: str, db: Session):
    """Clear OTP from user table after successful verification."""
    from models import User
    
    user = db.query(User).filter(User.mobile_no == mobile_no).first()
    if user:
        user.otp_code = None
        user.otp_created_at = None
        user.otp_expires_at = None
        db.commit()