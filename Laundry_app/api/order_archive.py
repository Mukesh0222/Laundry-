from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from db.session import get_db
from models.order_archive import OrderArchive, DeletionReason
from schemas.order_archive import OrderArchiveResponse, OrderArchiveSearch
from dependencies.auth import get_current_user, get_current_staff_user, get_current_admin_user
from models.user import User
from services.order_service import OrderService

router = APIRouter(prefix="/order-archive", tags=["order-archive"])

@router.delete("/orders/{order_id}")
def delete_archived_order(
    order_id: int,
    deletion_reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    try:
        print(f"Attempting to delete archived order {order_id} by user {current_user.user_id}")
        print(f"Deletion reason: {deletion_reason}")
        
        # Check if order exists in archive
        archived_order = db.query(OrderArchive).filter(OrderArchive.order_id == order_id).first()
        if not archived_order:
            print(f"Order {order_id} not found in archive")
            raise HTTPException(status_code=404, detail="Order not found in archive")
        
        print(f"Found archived order: {archived_order}")
        
        # Perform deletion
        db.delete(archived_order)
        db.commit()
        
        print(f"Successfully deleted archived order {order_id}")
        
        return {
            "message": "Order permanently deleted from archive",
            "order_id": order_id,
            "deletion_reason": deletion_reason,
            "deleted_by": current_user.user_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting archived order {order_id}: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete archived order: {str(e)}"
        )
    
@router.get("/", response_model=List[OrderArchiveResponse])
def get_archived_orders(
    original_order_id: Optional[int] = Query(None, description="Filter by original order ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    deletion_reason: Optional[DeletionReason] = Query(None, description="Filter by deletion reason"),
    deleted_by: Optional[int] = Query(None, description="Filter by user who deleted"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)  
):
    """Get archived orders with filtering"""
    archived_orders = OrderService.get_archived_orders(
        db=db,
        original_order_id=original_order_id,
        user_id=user_id,
        deletion_reason=deletion_reason,
        deleted_by=deleted_by,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit
    )
    
    return archived_orders

@router.get("/{archive_id}", response_model=OrderArchiveResponse)
def get_archived_order(
    archive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get specific archived order details"""
    archived_order = db.get(OrderArchive, archive_id)
    if not archived_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archived order not found")
    
    return archived_order

@router.post("/{archive_id}/restore", status_code=status.HTTP_200_OK)
def restore_archived_order(
    archive_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  
):
    """Restore an order from archive (Admin only)"""
    try:
        restored_order = OrderService.restore_order_from_archive(db, archive_id)
        
        return {
            "message": "Order restored successfully",
            "order_id": restored_order.id,
            "original_archive_id": archive_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/deletion-reasons/enum", response_model=dict)
def get_deletion_reasons():
    """Get all available deletion reasons for frontend"""
    return {
        "deletion_reasons": [reason.value for reason in DeletionReason]
    }