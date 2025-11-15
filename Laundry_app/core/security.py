from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
import random
import string
import secrets
# import jwt
import os

from core.config import settings

# pwd_context = CryptContext(schemes=["argon2", "sha256_crypt"], deprecated="auto")
pwd_context = CryptContext(schemes=["argon2","bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)

# def get_password_hash(password: str) -> str:
#     return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        print(f"Verifying password: {plain_password} against hash: {hashed_password}")
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"Password verification result: {result}")
        return result
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    try:
        hashed = pwd_context.hash(password)
        print(f"Password hash generated: {hashed}")
        return hashed
    except Exception as e:
        print(f"Password hashing error: {e}")
        raise

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    print(f" Creating token with SECRET_KEY: {settings.SECRET_KEY[:20]}...")
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    print(f" Token created: {encoded_jwt[:50]}...")
    return encoded_jwt

def generate_otp():
    """Generate 4-digit OTP"""
    return str(random.randint(1000, 9999)) 

# def verify_token(token: str) -> Union[str, None]:
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         return payload.get("sub")
#     except jwt.PyJWTError:
#         return None
    
def verify_token(token: str) -> Union[str, None]:
    try:
        print(f" Verifying token with SECRET_KEY: {settings.SECRET_KEY[:20]}...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str= payload.get("sub")
        print(f" Token verified. User ID: {user_id}")
        return user_id
    except jwt.PyJWTError as e:
        print(f" Token verification failed: {e}")
        return None