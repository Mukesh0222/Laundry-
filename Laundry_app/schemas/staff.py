from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class StaffRole(str, Enum):
    STAFF = "staff"
    DELIVERY_AGENT = "delivery_agent"
    MANAGER = "manager"

class StaffStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class StaffBase(BaseModel):
    name: str
    email: EmailStr
    mobile_no: Optional[str] = None
    role: StaffRole = StaffRole.STAFF
    status: StaffStatus = StaffStatus.ACTIVE

class StaffCreate(StaffBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_no: Optional[str] = None
    role: Optional[StaffRole] = None
    status: Optional[StaffStatus] = None
    password: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if v and len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class StaffResponse(StaffBase):
    user_id: int
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True