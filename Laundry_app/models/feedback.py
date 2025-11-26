# models/feedback.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
from db.session import Base

class Feedback(Base):
    __tablename__ = "feedbacks"
    
    feedback_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), index=True)
    
    # Rating (1-5 stars)
    rating = Column(Integer, nullable=False)
    
    # Feedback details
    comment = Column(Text, nullable=True)
    service_quality = Column(Integer, default=5)
    delivery_time = Column(Integer, default=5)
    staff_behavior = Column(Integer, default=5)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)