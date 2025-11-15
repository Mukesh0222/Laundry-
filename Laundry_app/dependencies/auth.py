from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from jose import JWTError, jwt
from db.session import get_db
from models.user import User
from Laundry_app.crud.crud_user import crud_user
from schemas.user import UserResponse
from core.security import verify_token
from core.config import settings
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

# def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
#     db: Session = Depends(get_db)
# ) -> UserResponse:
#     token = credentials.credentials
#     user_id = verify_token(token)
#     if user_id is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid authentication credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
    
#     user = crud_user.get_by_id(db, int(user_id))
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found"
#         )
#     if user.status != "active":
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Account is inactive"
#         )
#     return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    try:
        print(f" Authentication started")
        token = credentials.credentials
        print(f" Token received: {token[:20]}...")  # Print first 20 chars
        
        if not token or token == "null" or token == "undefined":
            print(" No token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication token provided"
            )
        
        # Print secret key info (for debugging)
        print(f" Token received: {token[:50]}...")
        print(f" SECRET_KEY exists: {bool(settings.SECRET_KEY)}")
        print(f" ALGORITHM: {settings.ALGORITHM}")
        
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        print(f" User ID from token: {user_id}")
        
        if user_id is None:
            print(" No user_id in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Convert user_id to int
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            print(f" Invalid user_id format: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format"
            )
        
        # Get user from database
        user = db.get(User, user_id_int)
        if user is None:
            print(f" User not found in database: {user_id_int}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
         # Check if user account is active
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive"
            )
        
        print(f" User authenticated: {user.name} (ID: {user.user_id}, Role: {user.role})")
        return user
        
    except JWTError as e:
        print(f" JWT Decode Error: {str(e)}")
        print(f" SECRET_KEY used: {settings.SECRET_KEY}")
        print(f" Token: {token[:50]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            # detail=f"Invalid token: {str(e)}"
            detail="Invalid token - Please login again"
        )
    except Exception as e:
        print(f" Unexpected auth error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
    
#  FIX: Change UserResponse to User
def get_current_staff_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify user has staff or admin role"""
    print(f" [STAFF-AUTH] Checking staff access for user: {current_user.email}")
    print(f" [STAFF-AUTH] User role: '{current_user.role}'")
    print(f" [STAFF-AUTH] User status: '{current_user.status}'")
    print(f" [STAFF-AUTH] Allowed roles: ['staff', 'admin']")
    
    # Check if role is in allowed list
    if current_user.role.lower() not in ["staff", "admin"]:
        print(f" [STAFF-AUTH] ACCESS DENIED - User role '{current_user.role}' not in allowed roles")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Staff or admin access required. Your role: {current_user.role}"
        )
    
    print(f" [STAFF-AUTH] ACCESS GRANTED - User has staff role")
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify user has admin role"""
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user