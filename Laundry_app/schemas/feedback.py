# schemas/feedback.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator
from datetime import datetime

class FeedbackBase(BaseModel):
    order_id: int
    rating: int
    comment: Optional[str] = None
    service_quality: Optional[int] = 5
    delivery_time: Optional[int] = 5
    staff_behavior: Optional[int] = 5

    @field_validator('rating', 'service_quality', 'delivery_time', 'staff_behavior')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None
    service_quality: Optional[int] = None
    delivery_time: Optional[int] = None
    staff_behavior: Optional[int] = None

    @field_validator('rating', 'service_quality', 'delivery_time', 'staff_behavior')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

class FeedbackResponse(FeedbackBase):
    feedback_id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FeedbackWithDetails(FeedbackResponse):
    user_name: Optional[str] = None
    order_token: Optional[str] = None