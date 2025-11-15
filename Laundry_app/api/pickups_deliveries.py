from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from db.session import get_db
from models.pickup_delivery import PickupDelivery, ServiceType, ServiceStatus
from schemas.pickup_delivery import PickupDeliveryCreate, PickupDeliveryResponse, PickupDeliveryUpdate
from dependencies.auth import get_current_user, get_current_staff_user
from models.user import User
from datetime import datetime
from crud import crud_pickup_delivery
from models.order import Order  
from models.pickup_delivery import PickupDelivery
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

def get_valid_service_types():
    """Get valid service types from database ENUM"""
    # Check your database schema
    valid_services = ['pickup', 'delivery', 'both']  # Example - adjust based on your DB
    return valid_services

# Add validation to your endpoint
@router.post("/")
def create_pickup_delivery(
    pickup_data: PickupDeliveryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    try:
        print(f" ENDPOINT REACHED!")
        print(f" User: {current_user.name} ID: {current_user.user_id}")
        
        #  PRINT RECEIVED DATA
        print(f" Received data: {pickup_data.dict()}")
        
        #  CHECK IF ORDER EXISTS
        order = db.get(Order, pickup_data.order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {pickup_data.order_id} not found"
            )
        print(f" Order found: {order.order_id}")
        
        #  CREATE PICKUP/DELIVERY RECORD
        db_pickup = PickupDelivery(**pickup_data.dict())
        print(f" PickupDelivery object created")
        
        db.add(db_pickup)
        print(f" Object added to session")
        
        db.commit()
        print(f" Transaction committed")
        
        db.refresh(db_pickup)
        print(f" Object refreshed from database")
        
        return {
            "success": True,
            "message": "Pickup/delivery scheduled successfully",
            "id": db_pickup.id,
            "order_id": db_pickup.order_id,
            "service_type": db_pickup.service_type,
            "status": db_pickup.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f" DATABASE ERROR: {str(e)}")
        print(f" ERROR TYPE: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pickup/delivery: {str(e)}"
        )
    
@router.get("/", response_model=List[PickupDeliveryResponse])
def read_pickups_deliveries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role in ["staff", "admin"]:
        statement = select(PickupDelivery).offset(skip).limit(limit)
    else:
        # Users can only see pickup/deliveries for their own orders
        from models.order import Order
        statement = select(PickupDelivery).join(Order).where(Order.user_id == current_user.user_id).offset(skip).limit(limit)
    
    pds = db.exec(statement).all()
    return pds

@router.get("/{pd_id}")
def read_pickup_delivery(
    pd_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pd = db.get(PickupDelivery, pd_id)
    if not pd:
        raise HTTPException(status_code=404, detail="Pickup/Delivery not found")
    
    # Check if user has access
    if current_user.role not in ["staff", "admin"]:
        from models.order import Order
        order = db.get(Order, pd.order_id)
        if order.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Return as dict to avoid validation issues
    return {
        "id": pd.id,
        "order_id": pd.order_id,
        "service_type": pd.service_type,
        "scheduled_date": pd.scheduled_date,
        "actual_date": pd.actual_date,
        "notes": pd.notes,
        "pickup_at": pd.pickup_at,
        "picked_at": pd.picked_at,
        "delivered_at": pd.delivered_at,
        "status": pd.status.upper() if pd.status else "PENDING",  # Convert to uppercase
        "created_at": pd.created_at if hasattr(pd, 'created_at') else datetime.utcnow(),
        "updated_at": pd.updated_at if hasattr(pd, 'updated_at') else datetime.utcnow()
    }

@router.put("/{pd_id}")
def update_pickup_delivery(
    pd_id: int,
    pd_update: PickupDeliveryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    try:
        pd = db.get(PickupDelivery, pd_id)
        if not pd:
            raise HTTPException(status_code=404, detail="Pickup/Delivery not found")
        
        print(f"Updating pickup/delivery {pd_id}")
        print(f"Update data: {pd_update.dict(exclude_unset=True)}")

        # Convert update data to dict and handle enum values
        update_data = pd_update.dict(exclude_unset=True)
        
        # Convert ServiceStatus enum to string if present
        safe_fields = ['notes', 'status']
        
        # Update only the provided fields
        for key in safe_fields:
            if key in update_data:
                value = update_data[key]
                print(f"Setting {key} = {value}")
                setattr(pd, key, value)
        
        # Skip datetime fields for now
        print("Skipping datetime fields (actual_date, pickup_at, picked_at, delivered_at) until database schema is fixed")
        
        db.add(pd)
        db.commit()
        
        # Return without refresh to avoid enum issues
        return {
            "success": True,
            "message": "Pickup/delivery updated successfully",
            "id": pd.id,
            "status": pd.status,
            "notes": pd.notes
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.post("/{pickup_id}/mark-picked", response_model=PickupDeliveryResponse)
def mark_as_picked_up(
    pickup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Mark pickup as picked up with timestamp"""
    pickup = crud_pickup_delivery.mark_picked_up(db, pickup_id)
    if not pickup:
        raise HTTPException(status_code=404, detail="Pickup not found or not a pickup service")
    return pickup

@router.post("/{delivery_id}/mark-delivered", response_model=PickupDeliveryResponse)
def mark_as_delivered(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Mark delivery as delivered with timestamp"""
    delivery = crud_pickup_delivery.mark_delivered(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found or not a delivery service")
    return delivery

@router.get("/order/{order_id}", response_model=List[PickupDeliveryResponse])
def get_by_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get all pickup/delivery schedules for an order"""
    pickups = crud_pickup_delivery.get_by_order(db, order_id)
    return pickups