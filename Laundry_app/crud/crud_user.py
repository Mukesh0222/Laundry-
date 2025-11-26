from sqlmodel import Session, select
from models.user import User
from datetime import datetime
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash, verify_password
from typing import Optional, List

class CRUDUser:
    # def get_by_mobile(self, db: Session, mobile_no: str):
    #     return db.exec(select(User).where(User.mobile_no == mobile_no)).first()
    
    def get_by_mobile(self, db: Session, mobile_no: str):
        """Get user by mobile number with status check"""
        print(f" Getting user by mobile: {mobile_no}")
        
        user = db.query(User).filter(User.mobile_no == mobile_no).first()
        
        if user:
            print(f" User found: {user.user_id}, Status: {user.status}")
            
            if user.status != "active":
                print(f" User is inactive. Status: {user.status}")
                return None
                
            return user
        else:
            print(f" User not found with mobile: {mobile_no}")
            return None
        
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        statement = select(User).where(User.email == email)
        return db.exec(statement).first()
    
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.get(User, user_id)
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        statement = select(User).offset(skip).limit(limit)
        return db.exec(statement).all()

    def create(self, db: Session, user_in: UserCreate) -> User:

        if isinstance(user_in, dict):
            mobile_no = user_in.get("mobile_no")
            email = user_in.get("email")
            name = user_in.get("name")
            password = user_in.get("password")
            role = user_in.get("role", "CUSTOMER")
            status = user_in.get("status", "active")
        else:
            
            mobile_no = user_in.mobile_no
            email = user_in.email
            name = user_in.name
            password = user_in.password
            role = user_in.role
            status = user_in.status

        
        existing_user = self.get_by_mobile(db, mobile_no)
        if existing_user:
            raise ValueError("Mobile number already registered")
        
        
        if email:
            existing_email = self.get_by_email(db, email)
            if existing_email:
                raise ValueError("Email already registered")
        
        
        hashed_password = get_password_hash(password)
        
        
        db_user = User(
            name=name,
            email=email,
            mobile_no=mobile_no,
            password=hashed_password,
            role=role,
            status=status
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update(self, db: Session, user_id: int, update_data: dict) -> Optional[User]:
        """
        Update user by ID - accepts dictionary directly
        """
        try:
            user = self.get_by_id(db, user_id)
            if not user:
                return None
            
            
            for field, value in update_data.items():
                if hasattr(user, field) and value is not None:
                    setattr(user, field, value)
            
            
            user.updated_at = datetime.utcnow()
            
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
            
        except Exception as e:
            db.rollback()
            print(f"Error updating user: {e}")
            return None

    def authenticate_by_name(self, db: Session, name: str, password: str):
        """Authenticate user by name and password"""
        print(f" Authenticating user by name: {name}")
        
        
        user = db.query(User).filter(User.name.ilike(name)).first()
        
        if user:
            print(f" User found: {user.user_id}")
            print(f" Verifying password...")
            
           
            if verify_password(password, user.password):
                print(f" Password verified successfully")
                return user
            else:
                print(f" Password verification failed")
        else:
            print(f" User not found with name: {name}")
        
        return None

    def authenticate_by_mobile(self, db: Session, mobile_no: str, password: str):
        user = db.query(User).filter(User.mobile_no == mobile_no).first()
        if user:
            print(f" User found: {user.user_id}, Status: {user.status}")
            print("DB password:", user.password)
            print("Input password:", password)
            
            if user.status != "active":
                print(f" User is inactive. Status: {user.status}")
                return None
            
            if not verify_password(password, user.password):
                print("Password verification failed")
                return None
                
            return user
        else:
            print("User not found")
            return None

    
    def update_otp(self, db: Session, mobile_no: str, otp: str) -> Optional[User]:
        user = self.get_by_mobile(db, mobile_no)
        if user:
            user.verified_otp = otp
            db.commit()
            db.refresh(user)
        return user

    def verify_otp(self, db: Session, mobile_no: str, otp: str) -> bool:
        user = self.get_by_mobile(db, mobile_no)
        if user and user.verified_otp == otp:
            user.verified_otp = None
            db.commit()
            return True
        return False

    def get_by_name(db: Session, name: str):
        from sqlmodel import select
        from models.user import User
        
        statement = select(User).where(User.name == name)
        return db.exec(statement).first()

    def get_customers(db: Session, skip: int = 0, limit: int = 100):
        from sqlmodel import select
        from models.user import User
        
        statement = select(User).where(User.role == "customer").offset(skip).limit(limit)
        return db.exec(statement).all()
    
crud_user = CRUDUser()