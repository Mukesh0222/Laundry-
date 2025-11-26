from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel
from typing import Optional

class Address(SQLModel, table=True):
    __tablename__ = "addresses"
    
    address_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")
    # address_type: str = Field(default="home", max_length=20)
    name: str = Field(max_length=150)
    mobile_no: str = Field(max_length=20)
    address_line1: str = Field(max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    # landmark: Optional[str] = Field(default=None, max_length=100)
    city: str = Field(max_length=100)
    state: str = Field(max_length=100)
    pincode: str = Field(max_length=10)
    # is_default: bool = Field(default=False)
    # status: str = Field(default="active", max_length=20)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    
    user: Optional["User"] = Relationship(back_populates="addresses")

    orders: List["Order"] = Relationship(back_populates="address")  


    class AddressResponse(BaseModel):
        id: int
        user_id: int
        address_line1: str
        address_line2: Optional[str] = None
        city: str
        state: str
        postal_code: str
        country: str = "India"
        is_primary: bool = False
        
        class Config:
            from_attributes = True