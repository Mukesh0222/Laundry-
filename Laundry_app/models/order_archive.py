from sqlmodel import SQLModel, Field, Column
from datetime import datetime
from typing import Optional, List
from sqlalchemy import JSON, Text
from enum import Enum

class DeletionReason(str, Enum):
    CUSTOMER_REQUEST = "customer_request"
    DUPLICATE_ORDER = "duplicate_order"
    PAYMENT_ISSUE = "payment_issue"
    SYSTEM_ERROR = "system_error"
    OTHER = "other"

class OrderArchive(SQLModel, table=True):
    __tablename__ = "order_archive"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    original_order_id: int = Field(index=True)
    user_id: int = Field(index=True)
    order_data: dict = Field(sa_column=Column(JSON))  
    order_items_data: dict = Field(sa_column=Column(JSON))  
    deletion_reason: DeletionReason
    deleted_by: int = Field(index=True)  
    deleted_by_role: str  
    notes: Optional[str] = Field(sa_column=Column(Text))
    deleted_at: datetime = Field(default_factory=datetime.utcnow)

class OrderItemsArchive(SQLModel, table=True):
    __tablename__ = "order_items_archive"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    original_item_id: int = Field(index=True)
    original_order_id: int = Field(index=True)
    archive_order_id: int = Field(index=True)  
    item_data: dict = Field(sa_column=Column(JSON))  
    deleted_at: datetime = Field(default_factory=datetime.utcnow)