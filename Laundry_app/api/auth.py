from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timedelta

from db.session import get_db
from schemas.user import UserLogin, Token, UserCreate, UserResponse, OTPVerify, PasswordReset
from Laundry_app.crud.crud_user import crud_user
from core.security import create_access_token, verify_password, generate_otp, verify_token, get_password_hash
from core.config import settings
from utils.otp_utils import generate_otp, store_otp_in_db, verify_otp_in_db, send_otp_via_sms, clear_otp_from_db
from models.user import User
from core.security import create_access_token

router = APIRouter()

@router.post("/login", response_model=dict)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user - if mobile provided, check OTP status; if verified, auto-login"""
    # If mobile number provided - OTP flow (passwordless)
    if user_data.mobile_no:
        print(f"OTP login attempt for mobile: {user_data.mobile_no}")
        
        # Check if user exists with this mobile
        user = crud_user.get_by_mobile(db, user_data.mobile_no)
        print(f"User found: {user}")

        if not user:
            print(f"New user detected, auto-registering: {user_data.mobile_no}")
            
            user_role = user_data.role if user_data.role else "customer"
            user_name = user_data.name if user_data.name else f"User_{user_data.mobile_no}"

            # Create new user directly using SQLModel (bypass UserCreate schema)
            from models.user import User
            db_user = User(
                name=user_name,
                mobile_no=user_data.mobile_no,
                email=f"{user_data.mobile_no}@laundry.com",
                password=get_password_hash("default123"),
                role=user_role,
                status="active"
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            user = db_user
            print(f"New user created: {user.user_id}, Name: {user.name}")             
        else:
            print(f"Existing user found: {user.name} (ID: {user.user_id})")
        
            #  CHECK IF USER IS OTP VERIFIED (AUTO-LOGIN)
            if user.verified_otp:  # Check if OTP was previously verified
                print(f" User {user.mobile_no} is OTP verified - AUTO LOGIN")
                
                # Generate token for auto-login
                access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    subject=user.user_id, expires_delta=access_token_expires
                )
                
                return {
                    "access_token": access_token, 
                    "token_type": "bearer",
                    "message": "Auto-login successful",
                    "user_id": user.user_id,
                    "name": user.name,
                    "role": user.role,
                    "mobile_no": user.mobile_no,
                    "auto_login": True  # Indicate auto-login
                }
        
        #  If not verified or new user, send OTP
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive"
            )  
        
        # Generate and send OTP (no password required)
        otp = generate_otp()
        store_otp_in_db(user_data.mobile_no, otp, db)  # Save OTP to database
        send_otp_via_sms(user_data.mobile_no, otp)  # Send SMS
        
        return {
            "message": "OTP sent to mobile number",
            "mobile_no": user_data.mobile_no,
            "next_step": "verify_otp",
            "role": user.role,
            "user_id": user.user_id,
            "auto_login": False  #  OTP required
        }
    
    # If name provided - password login (traditional)
    elif user_data.name and user_data.password:
        print(f"Password login attempt for user: {user_data.name}")
        
        # Check if password is provided
        if not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required for username login"
            )

        user = crud_user.authenticate_by_name(db, user_data.name, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive"
            )
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.user_id, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "message": "Login successful",
            "user_id": user.user_id,
            "name": user.name,
            "role": user.role,
            "mobile_no": user.mobile_no
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either mobile number (for OTP) or name with password must be provided"
        )
    
# @router.post("/login", response_model=dict)
# def login(user_data: UserLogin, db: Session = Depends(get_db)):
#     """Login user - if mobile provided, send OTP; if name, use password."""
#     # If mobile number provided - OTP flow (passwordless)
#     if user_data.mobile_no:
#         print(f"OTP login attempt for mobile: {user_data.mobile_no}")
        
#         # Check if user exists with this mobile
#         user = crud_user.get_by_mobile(db, user_data.mobile_no)
#         print(f"User found: {user}")

#         if not user:
#             print(f"New user detected, auto-registering: {user_data.mobile_no}")
            
#             user_role = user_data.role if user_data.role else "customer"

#             user_name = user_data.name if user_data.name else f"User_{user_data.mobile_no}"

#             # Create new user directly using SQLModel (bypass UserCreate schema)
#             from models.user import User
#             db_user = User(
#                 name=user_name,
#                 mobile_no=user_data.mobile_no,
#                 email=f"{user_data.mobile_no}@laundry.com",
#                 password=get_password_hash("default123"),
#                 role=user_role,
#                 status="active"
#             )
#             db.add(db_user)
#             db.commit()
#             db.refresh(db_user)
#             user = db_user
            
            
            
#         print(f"New user created: {user.user_id}, Name: {user.name}")             
        
#         if user.status != "active":
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Account is inactive"
#             )  
#     # Generate and send OTP (no password required)
#         otp = generate_otp()
#         store_otp_in_db(user_data.mobile_no, otp, db)  # Save OTP to database
#         send_otp_via_sms(user_data.mobile_no, otp)  # Send SMS
        
#         return {
#             "message": "OTP sent to mobile number",
#             "mobile_no": user_data.mobile_no,
#             "next_step": "verify_otp",
#             "role": user.role
#             # "user_id": user.user_id if user else None
#         }
    
#     # If name provided - password login (traditional)
#     elif user_data.name and user_data.password:
#         print(f"Password login attempt for user: {user_data.name}")
        
#         # Check if password is provided
#         if not user_data.password:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Password is required for username login"
#             )

#         user = crud_user.authenticate_by_name(db, user_data.name, user_data.password)
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Incorrect username or password"
#             )
        
#         if user.status != "active":
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Account is inactive"
#             )
#         access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#         access_token = create_access_token(
#             subject=user.user_id, expires_delta=access_token_expires
#         )
#         return {
#             "access_token": access_token, 
#             "token_type": "bearer",
#             "message": "Login successful",
#             "user_id": user.user_id,
#             "name": user.name,
#             "role": user.role,
#             "mobile_no": user.mobile_no
#         }
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Either mobile number (for OTP) or name with password must be provided"
#         )
    
# @router.post("/register", response_model=UserResponse)
# def register(user_data: UserCreate, db: Session = Depends(get_db)):
#     # Duplicate mobile check
#     existing_user = crud_user.get_by_mobile(db, user_data.mobile_no)
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Mobile number already registered"
#         )
#     user_data.password = get_password_hash(user_data.password)
#     user = crud_user.create(db, user_data)
#     return user

# @router.post("/forgot-password")
# def forgot_password(mobile_no: str, db: Session = Depends(get_db)):
#     user = crud_user.get_by_mobile(db, mobile_no)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )

#     otp = generate_otp()
#     crud_user.update_otp(db, mobile_no, otp)

#     # Send OTP via SMS or print for debug
#     print(f"OTP for {mobile_no}: {otp}")
#     return {"message": "OTP sent to your mobile number"}


# @router.post("/verify-otp")
# def verify_otp(
#     otp_data: OTPVerify,
#     db: Session = Depends(get_db)
# ):
#     """Verify OTP and return JWT token"""
#     try:
#         print(f" OTP verification for mobile: {otp_data.mobile_no}")
        
#         # Find user by mobile number
#         user = db.exec(select(User).where(User.mobile_no == otp_data.mobile_no)).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
        
#         # Verify OTP
#         if not user.otp_code or user.otp_code != otp_data.otp:
#             raise HTTPException(status_code=400, detail="Invalid OTP")
        
#         if user.otp_expires_at < datetime.utcnow():
#             raise HTTPException(status_code=400, detail="OTP expired")
        
#         # Clear OTP after successful verification
#         user.otp_code = None
#         user.otp_expires_at = None
#         db.add(user)
#         db.commit()
        
#         # IMPORTANT: Generate JWT token
#         from core.security import create_access_token
#         access_token = create_access_token(data={"sub": str(user.user_id)})
        
#         print(f" OTP verified successfully for: {user.mobile_no}")
        
#         return {
#             "access_token": access_token,
#             "token_type": "bearer",
#             "user_id": user.user_id,
#             "name": user.name,
#             "email": user.email,
#             "mobile_no": user.mobile_no,
#             "role": user.role
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f" OTP verification error: {str(e)}")
#         raise HTTPException(status_code=500, detail="OTP verification failed")

@router.post("/verify-otp")
def verify_otp(
    otp_data: OTPVerify,
    db: Session = Depends(get_db)
):
    """Verify OTP and return JWT token"""
    try:
        print(f" OTP verification for mobile: {otp_data.mobile_no}")
        print(f" OTP provided: {otp_data.otp}")
        
        # Find user by mobile number
        user = db.exec(select(User).where(User.mobile_no == otp_data.mobile_no)).first()
        if not user:
            print(f" User not found for mobile: {otp_data.mobile_no}")
            raise HTTPException(status_code=404, detail="User not found")
        
        print(f" User found: {user.name} (ID: {user.user_id})")
        print(f" Stored OTP: {user.otp_code}")
        print(f" OTP Created At: {user.otp_created_at}")
        print(f" OTP Expires At: {user.otp_expires_at}")
        
        # Verify OTP exists
        if not user.otp_code:
            print(f" No OTP stored for user: {user.mobile_no}")
            raise HTTPException(status_code=400, detail="No OTP found. Please request a new OTP.")
        
        # Verify OTP matches
        if user.otp_code != otp_data.otp:
            print(f" OTP mismatch. Stored: {user.otp_code}, Provided: {otp_data.otp}")
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Verify OTP not expired
        from datetime import datetime
        if user.otp_expires_at and user.otp_expires_at < datetime.utcnow():
            print(f" OTP expired. Expires at: {user.otp_expires_at}")
            raise HTTPException(status_code=400, detail="OTP expired")
        
        # Clear OTP after successful verification
        user.verified_otp = True 
        user.otp_code = None
        user.otp_expires_at = None

        db.add(user)
        db.commit()
        
        # Generate JWT token
        from core.security import create_access_token
        from datetime import timedelta
        from core.config import settings
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.user_id),  
            expires_delta=access_token_expires
        )
        
        print(f" OTP verified successfully for: {user.mobile_no}")
        print(f" Access token generated: {access_token[:50]}...")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "message": "Login successful",
            "user_id": user.user_id,
            "name": user.name,
            "mobile_no": user.mobile_no,
            "role": user.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f" OTP verification error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="OTP verification failed")

# @router.post("/resend-otp", response_model=dict)
# def resend_otp(user_data: UserLogin, db: Session = Depends(get_db)):
#     """Resend OTP with enhanced rate limiting"""
#     try:
#         if not user_data.mobile_no:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Mobile number is required"
#             )
        
#         print(f"OTP resend request for mobile: {user_data.mobile_no}")
        
#         from datetime import datetime, timedelta
#         current_time = datetime.utcnow()
        
#         # Check if user exists
#         user = crud_user.get_by_mobile(db, user_data.mobile_no)
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Mobile number not registered"
#             )
        
#         # Enhanced rate limiting for resend (5 minutes)
#         if user.otp_created_at:
#             time_since_last_otp = current_time - user.otp_created_at
#             if time_since_last_otp < timedelta(minutes=5):
#                 remaining_time = timedelta(minutes=5) - time_since_last_otp
#                 remaining_seconds = int(remaining_time.total_seconds())
#                 raise HTTPException(
#                     status_code=status.HTTP_429_TOO_MANY_REQUESTS,
#                     detail={
#                         "error": "Too many OTP requests",
#                         "message": f"Please wait {remaining_seconds} seconds before requesting new OTP",
#                         "retry_after": remaining_seconds
#                     }
#                 )
        
#         if user.status != "active":
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Account is inactive"
#             )
        
#         # Generate and send new OTP
#         otp = generate_otp()
#         store_otp_in_db(user_data.mobile_no, otp, db)
#         send_otp_via_sms(user_data.mobile_no, otp)
        
#         return {
#             "message": "New OTP sent to mobile number",
#             "mobile_no": user_data.mobile_no,
#             "next_step": "verify_otp",
#             "cooldown_period": 300  # 5 minutes in seconds
#         }
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"OTP resend error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="OTP resend failed"
#         )

@router.post("/resend-otp", response_model=dict)
def resend_otp(user_data: UserLogin, db: Session = Depends(get_db)):
    """Resend OTP with proper 1-minute rate limiting"""
    try:
        if not user_data.mobile_no:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile number is required"
            )

        print(f" OTP resend request for mobile: {user_data.mobile_no}")

        current_time = datetime.utcnow()

        #  Check if user exists
        user = crud_user.get_by_mobile(db, user_data.mobile_no)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mobile number not registered"
            )
        #  Ensure account is active
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive"
            )

        #  1-minute rate limit for OTP resend
        COOLDOWN_PERIOD = 180  # seconds
        if user.otp_created_at:
            time_since_last_otp = current_time - user.otp_created_at
            if time_since_last_otp < timedelta(seconds=COOLDOWN_PERIOD):
                remaining_time = timedelta(seconds=COOLDOWN_PERIOD) - time_since_last_otp
                remaining_seconds = int(remaining_time.total_seconds())
                remaining_minutes = remaining_seconds // 60
                remaining_secs = remaining_seconds % 60
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Too many OTP requests",
                        "message": f"Please wait {remaining_minutes} minutes {remaining_secs} seconds before requesting new OTP.",
                        "retry_after": remaining_seconds
                    }
                )

        #  Generate and send new OTP
        otp = generate_otp()
        store_otp_in_db(user_data.mobile_no, otp, db)
        send_otp_via_sms(user_data.mobile_no, otp)

        print(f" New OTP sent to {user_data.mobile_no}: {otp}")

        return {
            "message": "A new OTP has been sent successfully.",
            "mobile_no": user_data.mobile_no,
            "next_step": "verify_otp",
            "cooldown_period": COOLDOWN_PERIOD
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f" OTP resend error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP resend failed due to an internal error."
        )
    
# @router.post("/reset-password")
# def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
#     mobile_no = verify_token(reset_data.reset_token)
#     if not mobile_no or mobile_no != reset_data.mobile_no:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired reset token"
#         )

#     user = crud_user.get_by_mobile(db, reset_data.mobile_no)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )

#     user.password = get_password_hash(reset_data.new_password)
#     db.commit()

#     return {"message": "Password reset successfully"}



