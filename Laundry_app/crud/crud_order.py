from sqlmodel import Session, select
from typing import List, Optional
from models.order import Order
from schemas.order import OrderCreate, OrderUpdate, OrderStatus
from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User

class CRUDOrder:
    def get_by_id(self, db: Session, order_id: int) -> Optional[Order]:
        return db.get(Order, order_id)
    
    def get_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get all orders for a user with relationships"""
        statement = select(Order).where(Order.user_id == user_id)
        orders = db.exec(statement).all()
        # Access relationships
        for order in orders:
            print(f"Order: {order.Token_no}")
            if order.user:  
                print(f"User: {order.user.name}")
            if order.address:  
                print(f"Address: {order.address.address_line1}")
            print(f"Items count: {len(order.items)}")
        
        return orders
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
        statement = select(Order).offset(skip).limit(limit)
        return db.exec(statement).all()
    
    def get_by_order_number(self, db: Session, order_number: str) -> Optional[Order]:
        statement = select(Order).where(Order.order_number == order_number)
        return db.exec(statement).first()
    
    def create(self, db: Session, order_in: OrderCreate, user_id: int, current_user: User = None) -> Order:
        """Create new order with auto-confirm for admin/staff"""
        
        if current_user and current_user.role == "customer" and current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create order for this user"
            )
        
        
        initial_status = OrderStatus.PENDING
        if current_user and current_user.role in ["admin", "staff"]:
            initial_status = OrderStatus.CONFIRMED
            
        
        order_data = order_in.dict()
        order_data['user_id'] = user_id
        order_data['status'] = initial_status
        
        db_order = Order(**order_data)
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        print(f"Order created with status: {db_order.status} by {current_user.role if current_user else 'public'}")
        return db_order
    
    def update(self, db: Session, order_id: int, order_in: OrderUpdate) -> Optional[Order]:
        order = self.get_by_id(db, order_id)
        if order:
            update_data = order_in.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(order, field, value)
            db.add(order)
            db.commit()
            db.refresh(order)
        return order
    
    def delete(self, db: Session, order_id: int) -> bool:
        order = self.get_by_id(db, order_id)
        if order:
            db.delete(order)
            db.commit()
            return True
        return False

crud_order = CRUDOrder()