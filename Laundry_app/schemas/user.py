from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, constr, EmailStr, Field, field_validator
from models.user import UserRole as ModelUserRole, UserStatus as ModelUserStatus
from schemas.address import AddressResponse
import re

class UserBase(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    role: str
    mobile_no: Optional[str] = None
    status: str
    # address: Optional[str] = None
    # pincode: Optional[str] = None
    

class UserCreate(UserBase):
    password: str

    @field_validator('mobile_no')
    @classmethod
    def validate_mobile_no(cls, v):
        if not v:
            raise ValueError('Mobile number is required')
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_no: Optional[str] = None
    status: Optional[str] = None
    address_link_1: Optional[str] = None
    address_link_2: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    image_url: Optional[str] = None

    @field_validator('mobile_no')
    @classmethod
    def validate_mobile_no(cls, v):
        if not v:
            raise ValueError('Mobile number is required')
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v

    @field_validator('pincode')
    @classmethod
    def validate_pincode(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{6}$', v):
            raise ValueError('Pincode must be exactly 6 digits')
        return v
    
    @field_validator('mobile_no')
    @classmethod
    def validate_mobile_no(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v
    
    class Config:
        from_attributes = True
    
class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime
    addresses: List[AddressResponse] = [] 

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    name: Optional[str] = None 
    mobile_no: Optional[str] = None
    role: Optional[str] = None

    @field_validator('mobile_no')
    @classmethod
    def validate_mobile_no(cls, v):
        if not v:
            raise ValueError('Mobile number is required')
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v
    
class staffLogin(BaseModel):
    # name: Optional[str] = None 
    mobile_no: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    

    @field_validator('mobile_no')
    @classmethod
    def validate_mobile_no(cls, v):
        if not v:
            raise ValueError('Mobile number is required')
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v
    
class Token(BaseModel):
    access_token: str
    token_type: str
    # role: str = None

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

class OTPVerify(BaseModel):
    mobile_no: str
    otp: str
    
    @field_validator('mobile_no')
    @classmethod
    def validate_mobile_no(cls, v):
        if not v:
            raise ValueError('Mobile number is required')
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v
    
class PasswordReset(BaseModel):
    mobile_no: str
    new_password: str
    confirm_password: str
    reset_token: str

    @field_validator("new_password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v
    
    @field_validator("confirm_password")
    def passwords_match(cls, v, info):
        new_password = info.data.get("new_password")
        if new_password and v != new_password:
            raise ValueError("Passwords do not match.")
        return v