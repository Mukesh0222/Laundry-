from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session
from typing import List, Optional
import os
from datetime import datetime
from db.session import get_db
from schemas.user import UserResponse, UserUpdate, UserCreate 
from Laundry_app.crud.crud_user import crud_user
from dependencies.auth import get_current_user
from core.security import get_password_hash
from models.user import User

router = APIRouter()

@router.post("/", response_model=UserResponse)
def create_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new user (Admin/Staff only)
    """
    
    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Only staff and admin can create users."
        )
    
    existing_mobile = crud_user.get_by_mobile(db, user_data.mobile_no)
    if existing_mobile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number already registered"
        )
    
   
    hashed_password = get_password_hash(user_data.password)
    
    
    user_dict = user_data.dict()
    user_dict["password"] = hashed_password
    
    
    user = crud_user.create(db, user_dict)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return user

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    return current_user

# @router.put("/me", response_model=UserResponse)
# def update_my_profile(
#     user_data: UserUpdate,
#     db: Session = Depends(get_db),
#     current_user: UserResponse = Depends(get_current_user)
# ):
#     """
#     Update current user's own profile
#     """
#     try:
#         update_data = user_data.model_dump(exclude_unset=True, exclude_none=True)
#     except AttributeError:
#         update_data = user_data.dict(exclude_unset=True, exclude_none=True)
    
#     # Handle password update
#     if 'password' in update_data and update_data['password']:
#         update_data['hashed_password'] = get_password_hash(update_data['password'])
#         del update_data['password']
    
#     # Check if mobile number already exists
#     if 'mobile_no' in update_data and update_data['mobile_no']:
#         existing_mobile = crud_user.get_by_mobile(db, update_data['mobile_no'])
#         if existing_mobile and existing_mobile.user_id != current_user.user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Mobile number already registered by another user"
#             )
    
#     # Check if email already exists
#     if 'email' in update_data and update_data['email']:
#         existing_email = crud_user.get_by_email(db, update_data['email'])
#         if existing_email and existing_email.user_id != current_user.user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Email already registered by another user"
#             )
    
#     # Customers cannot change their role
#     if 'role' in update_data:
#         del update_data['role']
    
#     user = crud_user.update(db, current_user.user_id, update_data)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = crud_user.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    from sqlmodel import select
    statement = select(User).offset(skip).limit(limit)
    users = db.exec(statement).all()
    return users

# @router.put("/{user_id}", response_model=UserResponse)
# def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
#     """
#     Update user information
#     """
#     if current_user.role not in ["staff", "admin"] and current_user.user_id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not enough permissions"
#         )
    
#     # Check if mobile number already exists (if being updated)
#     if user_data.mobile_no:
#         existing_mobile = crud_user.get_by_mobile(db, user_data.mobile_no)
#         if existing_mobile and existing_mobile.user_id != user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Mobile number already registered by another user"
#             )
    
#     # Check if email already exists (if being updated)
#     if user_data.email:
#         existing_email = crud_user.get_by_email(db, user_data.email)
#         if existing_email and existing_email.user_id != user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Email already registered by another user"
#             )
    
#     user = crud_user.update(db, user_id, user_data)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
#     return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user information
    """
    
    if current_user.role not in ["staff", "admin"] and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    
    try:
        update_data = user_data.model_dump(exclude_unset=True, exclude_none=True)
    except AttributeError:
        
        update_data = user_data.dict(exclude_unset=True, exclude_none=True)
    
    
    if 'password' in update_data and update_data['password']:
        update_data['hashed_password'] = get_password_hash(update_data['password'])
        del update_data['password']
    
    
    if 'mobile_no' in update_data and update_data['mobile_no']:
        existing_mobile = crud_user.get_by_mobile(db, update_data['mobile_no'])
        if existing_mobile and existing_mobile.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile number already registered by another user"
            )
    
    
    if 'email' in update_data and update_data['email']:
        existing_email = crud_user.get_by_email(db, update_data['email'])
        if existing_email and existing_email.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user"
            )
    
    
    if current_user.role == "customer" and 'role' in update_data:
        del update_data['role']
    
    user = crud_user.update(db, user_id, update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

# @router.put("/{user_id}/profile", response_model=UserResponse)
# def update_user_profile(
#     user_id: int,
#     name: Optional[str] = None,
#     mobile_no: Optional[str] = None,
#     address_line1: Optional[str] = None,
#     address_line2: Optional[str] = None,
#     city: Optional[str] = None,
#     state: Optional[str] = None,
#     pincode: Optional[str] = None,
#     db: Session = Depends(get_db),
#     current_user: UserResponse = Depends(get_current_user)
# ):
#     """
#     Update user profile information (address and contact details)
#     """
#     # Users can only update their own profile
#     if current_user.user_id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You can only update your own profile"
#         )
    
#     # Prepare update data
#     update_data = {}
#     if name is not None:
#         update_data["name"] = name
#     if mobile_no is not None:
#         update_data["mobile_no"] = mobile_no
#     if address_line1 is not None:
#         update_data["address_line1"] = address_line1
#     if address_line2 is not None:
#         update_data["address_line2"] = address_line2
#     if city is not None:
#         update_data["city"] = city
#     if state is not None:
#         update_data["state"] = state
#     if pincode is not None:
#         if pincode and (len(pincode) != 6 or not pincode.isdigit()):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Pincode must be exactly 6 digits"
#             )
#         update_data["pincode"] = pincode
    
#     # Check if mobile number already exists
#     if mobile_no:
#         existing_mobile = crud_user.get_by_mobile(db, mobile_no)
#         if existing_mobile and existing_mobile.user_id != user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Mobile number already registered by another user"
#             )
    
#     user = crud_user.update(db, user_id, update_data)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return user

# @router.post("/{user_id}/upload-image")
# def upload_user_image(
#     user_id: int,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     current_user: UserResponse = Depends(get_current_user)
# ):
#     """
#     Upload user profile image
#     """
#     # Users can only upload their own image, staff/admin can upload for any user
#     if current_user.role not in ["staff", "admin"] and current_user.user_id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not enough permissions"
#         )
    
#     # Validate file type
#     allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
#     file_extension = os.path.splitext(file.filename)[1].lower()
#     if file_extension not in allowed_extensions:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Only image files (JPG, JPEG, PNG, GIF) are allowed"
#         )
    
#     try:
#         # Generate unique filename
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"user_{user_id}_{timestamp}{file_extension}"
#         file_path = os.path.join(UPLOAD_DIR, filename)
        
#         # Save the file
#         with open(file_path, "wb") as buffer:
#             content = file.file.read()
#             buffer.write(content)
        
#         # Update user record with image URL
#         image_url = f"/static/uploads/users/{filename}"
#         update_data = {"image_url": image_url}
#         user = crud_user.update(db, user_id, update_data)
        
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="User not found"
#             )
        
#         return {
#             "message": "Image uploaded successfully",
#             "image_url": image_url,
#             "user_id": user_id
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to upload image: {str(e)}"
#         )

# @router.get("/{user_id}/address")
# def get_user_address(
#     user_id: int,
#     db: Session = Depends(get_db),
#     current_user: UserResponse = Depends(get_current_user)
# ):
#     """
#     Get user address information
#     """
#     # Users can only view their own address, staff/admin can view any user's address
#     if current_user.role not in ["staff", "admin"] and current_user.user_id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not enough permissions"
#         )
    
#     user = crud_user.get_by_id(db, user_id)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return {
#         "user_id": user.user_id,
#         "name": user.name,
#         "address_line1": user.address_line1,
#         "address_line2": user.address_line2,
#         "city": user.city,
#         "state": user.state,
#         "pincode": user.pincode,
#         "mobile_no": user.mobile_no
#     }

# @router.delete("/{user_id}")
# def delete_user(
#     user_id: int,
#     db: Session = Depends(get_db),
#     current_user: UserResponse = Depends(get_current_user)
# ):
#     """
#     Delete user (Admin only)
#     """
#     # Only admin can delete users
#     if current_user.role != "admin":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only admin can delete users"
#         )
    
#     # Prevent self-deletion
#     if current_user.user_id == user_id:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Cannot delete your own account"
#         )
    
#     user = crud_user.get_by_id(db, user_id)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     success = crud_user.delete(db, user_id)
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to delete user"
#         )
    
#     return {"message": "User deleted successfully"}