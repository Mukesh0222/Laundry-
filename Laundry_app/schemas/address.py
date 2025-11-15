from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
import re

class AddressBase(BaseModel):
    # address_type: str = "home"
    name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    mobile_no: Optional[str] = None

    @validator("mobile_no")
    def validate_mobile_no(cls, v):
        if v is None or v == "":
            return v
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Mobile number must be exactly 10 digits")
        return v
    
    @validator("pincode")
    def validate_pincode(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Pincode must be exactly 6 digits")
        return v
    
class AddressCreate(AddressBase):
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    # state: str
    pincode: str
    # is_default: bool = False

    @validator("pincode")
    def check_pincode(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Invalid pincode — must be 6 digits")
        return v
    
    @validator("mobile_no")
    def validate_mobile_no(cls, v):
        if v is None or v == "":
            return v
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Mobile number must be exactly 10 digits")
        return v

class AddressUpdate(BaseModel):
    # address_type: Optional[str] = None
    name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    mobile_no: Optional[str] = None
    # is_default: Optional[bool] = None

    @validator("pincode")
    def validate_pincode(cls, v):
        if v is None or v == "":
            return v
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Pincode must be exactly 6 digits")
        return v

    @validator("mobile_no")
    def validate_mobile_no(cls, v):
        if v is None or v == "":
            return v
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Mobile number must be exactly 10 digits")
        return v
    
class AddressResponse(AddressBase):
    address_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    # is_default: bool

    class Config:
        from_attributes = True