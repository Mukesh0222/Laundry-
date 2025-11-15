from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from models.pickup_delivery import ServiceType, ServiceStatus
from enum import Enum as PyEnum

class ServiceType(PyEnum):
    PICKUP = "PICKUP"            
    DELIVERY = "DELIVERY"

class ServiceStatus(PyEnum):
    SCHEDULED = "SCHEDULED"      
    PENDING = "PENDING"          
    IN_PROGRESS = "IN_PROGRESS"  
    COMPLETED = "COMPLETED"      
    CANCELLED = "CANCELLED" 

class PickupDeliveryBase(BaseModel):
    order_id: int
    service_type: ServiceType 
    scheduled_date: datetime
    notes: Optional[str] = None

    class Config:
        use_enum_values = True

class PickupDeliveryCreate(PickupDeliveryBase):
    pass

class PickupDeliveryUpdate(BaseModel):
    actual_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    pickup_at: Optional[datetime] = None
    picked_at: Optional[datetime] = None  
    delivered_at: Optional[datetime] = None 

    class Config:
        arbitrary_types_allowed = True


class PickupDeliveryResponse(PickupDeliveryBase):
    id: int
    actual_date: Optional[datetime] = None
    pickup_at: Optional[datetime]
    picked_at: Optional[datetime]  
    delivered_at: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime

    @validator('status', pre=True)
    def validate_status(cls, v):
        # Convert database value to expected case
        status_map = {
            'pending': 'PENDING',
            'scheduled': 'SCHEDULED', 
            'in_progress': 'IN_PROGRESS',
            'completed': 'COMPLETED',
            'cancelled': 'CANCELLED'
        }
        return status_map.get(v, v)

    class Config:
        from_attributes = True