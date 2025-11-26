# from sqlmodel import SQLModel, Field, Column, Relationship
# from typing import Optional, List
# from datetime import datetime
# from enum import Enum
# from sqlalchemy.dialects.mysql import ENUM as MySQLEnum

# class OrderStatus(str, Enum):
#     PENDING = "pending"
#     CONFIRMED = "confirmed"
#     IN_PROGRESS = "in_progress"
#     PROCESSED = "processed"
#     READY = "ready"  
#     PICKED_UP  = "picked_up"
#     COMPLETED = "completed"
#     CANCELLED = "cancelled"
#     PICKED = "picked"

# class ServiceType(str, Enum):
#     WASH_IRON = "wash_iron"
#     DRY_CLEANING = "dry_cleaning"
#     WASH_ONLY = "wash_only"
#     IRON_ONLY = "iron_only"

# class Order(SQLModel, table=True):
#     __tablename__ = "orders"
    
#     order_id: Optional[int] = Field(default=None, primary_key=True)
#     user_id: int = Field(foreign_key="users.user_id")
#     address_id: int = Field(foreign_key="addresses.address_id")
#     Token_no: str = Field(max_length=50, unique=True, index=True)
#     # service: ServiceType = Field(sa_column=Column(MySQLEnum(ServiceType)))  
#     service: str = Field()
#     status: str = Field(default="pending") 
    
#     picked_at: Optional[datetime] = Field(default=None)
#     delivered_at: Optional[datetime] = Field(default=None)
#     cancelled_at: Optional[datetime] = Field(default=None)
    
#     picked_by: Optional[str] = Field(default=None, max_length=150)
#     delivered_by: Optional[str] = Field(default=None, max_length=150)
#     cancelled_by: Optional[str] = Field(default=None, max_length=150)
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#     updated_at: datetime = Field(default_factory=datetime.utcnow)
#     created_by: Optional[str] = Field(default=None, max_length=150)
#     updated_by: Optional[str] = Field(default=None, max_length=150)

   
#     user: Optional["User"] = Relationship(back_populates="orders")  
#     address: Optional["Address"] = Relationship(back_populates="orders")  
#     items: List["OrderItem"] = Relationship(back_populates="order", cascade_delete=True) 
#     # feedbacks: List["Feedback"] = Relationship(back_populates="order")



from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.mysql import ENUM as MySQLEnum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    PROCESSED = "processed"
    READY = "ready"  
    PICKED_UP  = "picked_up"
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
    
    picked_at: Optional[datetime] = Field(default=None)
    delivered_at: Optional[datetime] = Field(default=None)
    cancelled_at: Optional[datetime] = Field(default=None)
    
    picked_by: Optional[str] = Field(default=None, max_length=150)
    delivered_by: Optional[str] = Field(default=None, max_length=150)
    cancelled_by: Optional[str] = Field(default=None, max_length=150)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(default=None, max_length=150)
    updated_by: Optional[str] = Field(default=None, max_length=150)

   
    user: Optional["User"] = Relationship(back_populates="orders")  
    address: Optional["Address"] = Relationship(back_populates="orders")  
    # ✅ FIXED: Removed cascade_delete
    items: List["OrderItem"] = Relationship(back_populates="order") 
    # feedbacks: List["Feedback"] = Relationship(back_populates="order")