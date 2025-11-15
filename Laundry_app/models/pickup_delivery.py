from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum
# from sqlalchemy.dialects.mysql import ENUM

class ServiceType(str, Enum):
    PICKUP = "pickup"
    DELIVERY = "delivery"

class ServiceStatus(str, Enum):
    SCHEDULED = "scheduled"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PickupDelivery(SQLModel, table=True):
    __tablename__ = "pickups_deliveries"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.order_id")
    scheduled_date: datetime
    actual_date: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=255)
    pickup_at: Optional[datetime] = Field(default=None)
    picked_at: Optional[datetime] = Field(default=None)
    delivered_at: Optional[datetime] = Field(default=None) 
    service_type: str
    status: str = Field(default="PENDING")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
