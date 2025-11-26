from sqlmodel import Session
from typing import Optional
from core.security import verify_password, create_access_token, generate_otp
from Laundry_app.crud.crud_user import crud_user
from models.user import User
from datetime import timedelta
from core.config import settings

class AuthService:
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        user = crud_user.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    
    def create_access_token_for_user(self, user: User) -> str:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.user_id, "role": user.role},
            expires_delta=access_token_expires
        )
        return access_token
    
    def generate_and_save_otp(self, db: Session, user: User) -> str:
        otp = generate_otp()
        
        user.verified_otp = otp
        db.add(user)
        db.commit()
        return otp
    
    def verify_otp(self, db: Session, user: User, otp: str) -> bool:
        if user.verified_otp == otp:
            user.verified_otp = None
            db.add(user)
            db.commit()
            return True
        return False

auth_service = AuthService()