from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
from models.order import OrderStatus, ServiceType
from enum import Enum
from schemas.order_item import OrderItemCreate, OrderItemResponse

class ServiceType(str, Enum):
    WASH_IRON = "wash_iron"
    DRY_CLEANING = "dry_cleaning"
    WASH_ONLY = "wash_only"
    IRON_ONLY = "iron_only"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderBase(BaseModel):
    # address_id: int
    address_line1: Optional[str] = None 
    address_line2: Optional[str] = None  
    city: Optional[str] = None   
    state: Optional[str] = None   
    pincode: Optional[str] = None   
    landmark: Optional[str] = None 
    status: Optional[OrderStatus] = OrderStatus.PENDING

class OrderCreate(OrderBase):
    service: ServiceType
    items: List[OrderItemCreate]
    
    @validator("items")
    def validate_items_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one item is required in the order")
        return v
    

class StaffOrderCreate(BaseModel):
    # user_id: int
    # address_id: Optional[int] = None 
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None 
    state: Optional[str] = None   
    pincode: Optional[str] = None  
    landmark: Optional[str] = None
    status: Optional[OrderStatus] = OrderStatus.PENDING
    service: ServiceType
    items: List[OrderItemCreate]

    @validator("items")
    def validate_items_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one item is required in the order")
        return v

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    service: Optional[ServiceType] = None
    Token_no: str

class OrderResponse(OrderBase):
    order_id: int
    user_id: int
    address_id: int
    Token_no: str
    service: ServiceType
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    # order_items: List[OrderItemResponse] = []

    # Include relationship data
    user_name: Optional[str] = None
    user_mobile: Optional[str] = None
    address_details: Optional[dict] = None
    items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True

    # Add this method to populate response with actual data
    @classmethod
    def from_orm(cls, obj):
        # Get the basic object data
        data = super().from_orm(obj)
        
        # If we have address relationship, populate address_details
        if hasattr(obj, 'address') and obj.address:
            data.address_details = {
                "address_line1": obj.address.address_line1,
                "address_line2": obj.address.address_line2,
                "city": obj.address.city,
                "state": obj.address.state,
                "pincode": obj.address.pincode,
                # "landmark": obj.address.landmark
            }
        
        # If we have user relationship, populate user details
        if hasattr(obj, 'user') and obj.user:
            data.user_name = obj.user.name
            data.user_mobile = obj.user.mobile_no
        
        # FIX: Populate items if order items relationship exists
        if hasattr(obj, 'items') and obj.items:
            data.items = [OrderItemResponse.from_orm(item) for item in obj.items]
            data.order_items = data.items  # Also populate order_items

        return data

