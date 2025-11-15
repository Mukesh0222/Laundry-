# from fastapi import Depends, HTTPException, status
# from sqlmodel import Session
# from db.session import get_db
# from Laundry_app.crud.crud_user import crud_user
# from dependencies.auth import get_current_user

# def get_current_customer(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
#     """
#     Get current customer - ensures the user is a customer
#     """
#     if current_user.role != "customer":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access denied. Customer account required."
#         )
    
#     return current_user