from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.mysql import ENUM as MySQLEnum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PICKED = "picked"

class ServiceType(str, Enum):
    WASH_IRON = "wash_iron"
    DRY_CLEANING = "dry_cleaning"
    WASH_ONLY = "wash_only"
    IRON_ONLY = "iron_only"

class Order(SQLModel, table=True):
    __tablename__ = "orders"
    
    order_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")
    address_id: int = Field(foreign_key="addresses.address_id")
    Token_no: str = Field(max_length=50, unique=True, index=True)
    # service: ServiceType = Field(sa_column=Column(MySQLEnum(ServiceType)))  
    service: str = Field()
    status: str = Field(default="pending") 
    # status: OrderStatus = Field(sa_column=Column(MySQLEnum(OrderStatus)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(default=None, max_length=150)
    updated_by: Optional[str] = Field(default=None, max_length=150)

    #  Relationships
    user: Optional["User"] = Relationship(back_populates="orders")  #  Order-User relationship
    address: Optional["Address"] = Relationship(back_populates="orders")  #  Order-Address relationship
    items: List["OrderItem"] = Relationship(back_populates="order", cascade_delete=True)  #  Order-OrderItem relationship