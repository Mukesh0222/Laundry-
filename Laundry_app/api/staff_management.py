from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
import bcrypt
from starlette import status

from db.session import get_db
from models.user import User, UserRole
from schemas.staff import StaffCreate, StaffUpdate, StaffResponse
from dependencies.auth import get_current_user

router = APIRouter(tags=["Staff Management"])

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


@router.get("/", response_model=List[StaffResponse])
async def get_all_staff(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all staff members (users with role 'staff')
    with pagination and filtering
    """
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        
        staff_roles = [UserRole.STAFF]
        
        statement = select(User).where(User.role.in_(staff_roles))
        
        
        if role:
            statement = statement.where(User.role == role)
        if status_filter:
            statement = statement.where(User.status == status_filter)
        
        
        statement = statement.offset(skip).limit(limit)
        
        
        result = db.execute(statement)
        staff_members = result.scalars().all()
        
        return staff_members
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching staff: {str(e)}"
        )


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific staff member by ID
    """
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        staff = db.get(User, staff_id)
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        
        if staff.role != UserRole.STAFF:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a staff member"
            )
        
        return staff
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching staff: {str(e)}"
        )


@router.post("/", response_model=StaffResponse)
async def create_staff(
    staff_data: StaffCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create staff members"
        )
    
    try:
        
        statement = select(User).where(User.email == staff_data.email)
        result = db.execute(statement)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        
        hashed_password = hash_password(staff_data.password)
        
        new_staff = User(
            name=staff_data.name,
            email=staff_data.email,
            mobile_no=staff_data.mobile_no,
            password=hashed_password,
            role=staff_data.role.value,
            status=staff_data.status.value,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_staff)
        db.commit()
        db.refresh(new_staff)
        
        return new_staff
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating staff: {str(e)}"
        )


@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: int,
    staff_data: StaffUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a staff member
    """
    # FIX: Only admin can update staff
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        staff = db.get(User, staff_id)
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        
        if staff.role != UserRole.STAFF:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a staff member"
            )
        
        
        if staff_data.email and staff_data.email != staff.email:
            statement = select(User).where(User.email == staff_data.email)
            result = db.execute(statement)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        
        update_data = staff_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == 'password' and value:
                
                setattr(staff, field, hash_password(value))
            elif field in ['role', 'status'] and value:
                
                setattr(staff, field, value.value)
            elif value is not None:
                setattr(staff, field, value)
        
        staff.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(staff)
        
        return staff
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating staff: {str(e)}"
        )


@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete staff members"
        )
    
    try:
        staff = db.get(User, staff_id)
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        
        if staff.role != UserRole.STAFF:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a staff member"
            )
        
        
        if staff.user_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        
        staff.status = "inactive"
        staff.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Staff member deleted successfully",
            "staff_id": staff_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting staff: {str(e)}"
        )


@router.get("/role/{role}", response_model=List[StaffResponse])
async def get_staff_by_role(
    role: UserRole,
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        
        if role != UserRole.STAFF:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role for staff management"
            )
        
        statement = select(User).where(User.role == role.value)
        
        if status_filter:
            statement = statement.where(User.status == status_filter)
        else:
            
            statement = statement.where(User.status == "active")
        
        
        result = db.execute(statement)
        staff_members = result.scalars().all()
        
        return staff_members
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching staff by role: {str(e)}"
        )


# @router.get("/stats/summary")
# async def get_staff_stats(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get staff statistics summary
#     """
   
#     if current_user.role != UserRole.ADMIN:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not enough permissions"
#         )
    
#     try:
#         staff_roles = [UserRole.STAFF]  
        
        
#         statement = select(User).where(User.role.in_(staff_roles))
#         result = db.execute(statement)
#         total_staff = result.scalars().all()
        
        
#         staff_by_role = {}
#         for role in staff_roles:
#             statement = select(User).where(
#                 User.role == role.value,
#                 User.status == "active"
#             )
#             result = db.execute(statement)
#             count = result.scalars().all()
#             staff_by_role[role.value] = len(count)
        
       
#         active_statement = select(User).where(
#             User.role.in_(staff_roles),
#             User.status == "active"
#         )
#         active_result = db.execute(active_statement)
#         active_staff = active_result.scalars().all()
        
#         inactive_statement = select(User).where(
#             User.role.in_(staff_roles),
#             User.status == "inactive"
#         )
#         inactive_result = db.execute(inactive_statement)
#         inactive_staff = inactive_result.scalars().all()
        
#         return {
#             "total_staff": len(total_staff),
#             "active_staff": len(active_staff),
#             "inactive_staff": len(inactive_staff),
#             "by_role": staff_by_role
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error fetching staff statistics: {str(e)}"
#         )
    
    