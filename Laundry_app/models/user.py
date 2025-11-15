from sqlmodel import SQLModel, Field, Column, Relationship, DateTime, String
from typing import List, Optional
from datetime import datetime
from sqlalchemy.dialects.mysql import ENUM
from sqlalchemy import Enum as SQLEnum
import enum

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    STAFF = "staff"
    ADMIN = "admin"

class UserStatus(str, ENUM):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    user_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=150)
    email: str = Field(max_length=255, unique=True, index=True)
    mobile_no: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(max_length=255)
    role: str = Field(default="customer", max_length=50)
    image_url: Optional[str] = Field(default= None, max_length=500)     
    verified_otp: Optional[str] = Field(default=None, max_length=10)
    reset_password: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="active", max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    otp_code: Optional[str] = Field(default=None)
    otp_created_at: Optional[datetime] = Field(default=None)
    otp_expires_at: Optional[datetime] = Field(default=None)

    addresses: List["Address"] = Relationship(back_populates="user", cascade_delete=True)
    
    orders: List["Order"] = Relationship(back_populates="user")  
