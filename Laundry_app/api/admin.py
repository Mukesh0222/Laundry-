from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from db.session import get_db
from models.user import User
from core.security import get_password_hash
from typing import List

router = APIRouter()

@router.post("/reset-all-passwords")
def reset_all_passwords(
    new_password: str,
    db: Session = Depends(get_db)
):
    """Admin endpoint to reset all user passwords (use for development only)"""
    
    # Get all users
    statement = select(User)
    users = db.exec(statement).all()
    
    reset_count = 0
    for user in users:
        user.password = get_password_hash(new_password)
        reset_count += 1
    
    db.commit()
    
    return {
        "message": f"Passwords reset for {reset_count} users",
        "new_password": new_password
    }

@router.post("/reset-user-password")
def reset_user_password(
    mobile_no: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """Reset password for a specific user"""
    statement = select(User).where(User.mobile_no == mobile_no)
    user = db.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.password = get_password_hash(new_password)
    db.commit()
    
    return {
        "message": "Password reset successfully",
        "user_id": user.user_id,
        "mobile_no": user.mobile_no
    }

@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    """Get all users (for debugging)"""
    statement = select(User)
    users = db.exec(statement).all()
    
    user_list = []
    for user in users:
        user_list.append({
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "mobile_no": user.mobile_no,
            "password_hash": user.password[:50] + "..." if user.password else None,
            "status": user.status
        })
    
    return user_list