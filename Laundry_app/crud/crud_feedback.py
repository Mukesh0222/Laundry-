# crud/crud_feedback.py
from sqlalchemy.orm import Session
from typing import List, Optional
from models.feedback import Feedback
from models.order import Order
from models.user import User

class FeedbackCRUD:
    
    def create_feedback(self, db: Session, feedback_data: dict):
        """Create new feedback"""
        # Check if feedback already exists for this order
        existing = db.query(Feedback).filter(Feedback.order_id == feedback_data['order_id']).first()
        if existing:
            raise ValueError("Feedback already exists for this order")
        
        # Check if order exists
        order = db.query(Order).filter(Order.order_id == feedback_data['order_id']).first()
        if not order:
            raise ValueError("Order not found")
        
        feedback = Feedback(**feedback_data)
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
    
    def create_or_update_feedback(self, db: Session, feedback_data: dict):
        """Create new feedback or update existing one"""
        try:
            # Check if feedback already exists for this order
            existing = db.query(Feedback).filter(Feedback.order_id == feedback_data['order_id']).first()
            
            if existing:
                # Update existing feedback
                print(f"Updating existing feedback for order {feedback_data['order_id']}")
                for field, value in feedback_data.items():
                    if hasattr(existing, field) and field != 'feedback_id':  # Don't update ID
                        setattr(existing, field, value)
                db.commit()
                db.refresh(existing)
                return existing
            else:
                # Create new feedback
                print(f"Creating new feedback for order {feedback_data['order_id']}")
                
                # Check if order exists
                order = db.query(Order).filter(Order.order_id == feedback_data['order_id']).first()
                if not order:
                    raise ValueError("Order not found")
                
                feedback = Feedback(**feedback_data)
                db.add(feedback)
                db.commit()
                db.refresh(feedback)
                return feedback
                
        except Exception as e:
            db.rollback()
            print(f"Error in create_or_update_feedback: {str(e)}")
            raise
        
    def get_feedback_by_id(self, db: Session, feedback_id: int):
        return db.query(Feedback).filter(Feedback.feedback_id == feedback_id).first()
    
    def get_feedback_by_order(self, db: Session, order_id: int):
        return db.query(Feedback).filter(Feedback.order_id == order_id).first()
    
    def get_feedbacks_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100):
        return db.query(Feedback).filter(Feedback.user_id == user_id).offset(skip).limit(limit).all()
    
    def get_all_feedbacks(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(Feedback).offset(skip).limit(limit).all()
    
    def update_feedback(self, db: Session, feedback_id: int, update_data: dict):
        feedback = self.get_feedback_by_id(db, feedback_id)
        if not feedback:
            return None
        
        for field, value in update_data.items():
            if hasattr(feedback, field):
                setattr(feedback, field, value)
        
        db.commit()
        db.refresh(feedback)
        return feedback
    
    def delete_feedback(self, db: Session, feedback_id: int):
        feedback = self.get_feedback_by_id(db, feedback_id)
        if not feedback:
            return False
        
        feedback.is_active = False
        db.commit()
        return True

feedback_crud = FeedbackCRUD()