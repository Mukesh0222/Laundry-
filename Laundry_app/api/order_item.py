from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional

from db.session import get_db
from models.order_item import OrderItem, OrderItemStatus, ServiceType 
from schemas.order_item import OrderItemResponse, OrderItemUpdate
from dependencies.auth import get_current_user, get_current_staff_user
from models.user import User

router = APIRouter()

@router.get("/order/{order_id}", response_model=List[OrderItemResponse])
def read_order_items(
    order_id: int,
    service: Optional[ServiceType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models.order import Order
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if current_user.role not in ["staff", "admin"] and order.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    statement = select(OrderItem).where(OrderItem.order_id == order_id)
    items = db.exec(statement).all()
    return items

@router.get("/{item_id}", response_model=OrderItemResponse)
def read_order_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    
    
    from models.order import Order
    order = db.get(Order, item.order_id)
    if current_user.role not in ["staff", "admin"] and order.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return item

@router.put("/{item_id}", response_model=OrderItemResponse)
def update_order_item(
    item_id: int,
    item_update: OrderItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    
    for key, value in item_update.dict(exclude_unset=True).items():
        setattr(item, key, value)
    
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

