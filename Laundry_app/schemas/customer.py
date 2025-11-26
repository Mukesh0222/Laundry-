from pydantic import BaseModel, Field,  field_validator
from typing import List, Optional
from datetime import datetime
from schemas.address import AddressResponse

class CustomerCreate(BaseModel):
    name: str
    mobile_no: str
    password: str
    email: Optional[str] = None
    image_url: Optional[str] = None

class CustomerResponse(BaseModel):
    user_id: int
    name: str
    mobile_no: str
    email: Optional[str] = None
    image_url: Optional[str] = None
    role: str
    status: str
    addresses: List[AddressResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    
    @field_validator('mobile_no', mode='before')
    @classmethod
    def validate_mobile_no(cls, v):
        if v is None:
            return "0000000000"  
        return str(v)
    
    class Config:
        from_attributes = True
        populate_by_name = True

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    mobile_no: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None

class CustomerLogin(BaseModel):
    name: Optional[str] = None
    mobile_no: Optional[str] = None
    