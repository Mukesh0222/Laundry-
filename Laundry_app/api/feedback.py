# api/feedback.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from db.session import get_db
from schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackUpdate
from crud.crud_feedback import feedback_crud
from dependencies.auth import get_current_user

router = APIRouter()

@router.post("/feedbacks/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    try:
        ratings = [
            feedback_data.rating,
            feedback_data.service_quality or 5,
            feedback_data.delivery_time or 5,
            feedback_data.staff_behavior or 5
        ]
        
        for rating in ratings:
            if rating < 1 or rating > 5:
                raise HTTPException(
                    status_code=400, 
                    detail="All ratings must be between 1 and 5"
                )
        feedback_dict = feedback_data.dict()
        feedback_dict['user_id'] = current_user.user_id
        
        feedback = feedback_crud.create_or_update_feedback(db, feedback_dict)        
        return FeedbackResponse.from_orm(feedback)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/feedbacks/", response_model=List[FeedbackResponse])
def get_all_feedbacks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    feedbacks = feedback_crud.get_all_feedbacks(db, skip=skip, limit=limit)
    return [FeedbackResponse.from_orm(feedback) for feedback in feedbacks]

@router.get("/feedbacks/{feedback_id}", response_model=FeedbackResponse)
def get_feedback(feedback_id: int, db: Session = Depends(get_db)):
    feedback = feedback_crud.get_feedback_by_id(db, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return FeedbackResponse.from_orm(feedback)

@router.get("/orders/{order_id}/feedback", response_model=FeedbackResponse)
def get_feedback_by_order(order_id: int, db: Session = Depends(get_db)):
    feedback = feedback_crud.get_feedback_by_order(db, order_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found for this order")
    return FeedbackResponse.from_orm(feedback)

@router.get("/users/{user_id}/feedbacks", response_model=List[FeedbackResponse])
def get_user_feedbacks(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    feedbacks = feedback_crud.get_feedbacks_by_user(db, user_id, skip=skip, limit=limit)
    return [FeedbackResponse.from_orm(feedback) for feedback in feedbacks]

@router.put("/feedbacks/{feedback_id}", response_model=FeedbackResponse)
def update_feedback(
    feedback_id: int,
    feedback_data: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    feedback = feedback_crud.get_feedback_by_id(db, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    if feedback.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this feedback")
    
    updated_feedback = feedback_crud.update_feedback(db, feedback_id, feedback_data.dict(exclude_unset=True))
    return FeedbackResponse.from_orm(updated_feedback)

@router.delete("/feedbacks/{feedback_id}")
def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    feedback = feedback_crud.get_feedback_by_id(db, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    if feedback.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this feedback")
    
    success = feedback_crud.delete_feedback(db, feedback_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return {"message": "Feedback deleted successfully"}