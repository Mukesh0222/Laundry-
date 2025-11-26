from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from models.order_archive import DeletionReason

class OrderArchiveCreate(BaseModel):
    original_order_id: int
    deletion_reason: DeletionReason
    notes: Optional[str] = None

class OrderArchiveResponse(BaseModel):
    id: int
    original_order_id: int
    user_id: int
    order_data: Dict[str, Any]
    order_items_data: Dict[str, Any]
    deletion_reason: DeletionReason
    deleted_by: int
    deleted_by_role: str
    notes: Optional[str]
    deleted_at: datetime

    class Config:
        from_attributes = True

class OrderArchiveSearch(BaseModel):
    original_order_id: Optional[int] = None
    user_id: Optional[int] = None
    deletion_reason: Optional[DeletionReason] = None
    deleted_by: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None