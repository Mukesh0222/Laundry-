from sqlmodel import Session, select
from typing import List, Optional
from models.order import Order
from schemas.order import OrderCreate, OrderUpdate

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
            if order.user:  #  Check if user relationship exists
                print(f"User: {order.user.name}")
            if order.address:  #  Check if address relationship exists
                print(f"Address: {order.address.address_line1}")
            print(f"Items count: {len(order.items)}")
        
        return orders
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
        statement = select(Order).offset(skip).limit(limit)
        return db.exec(statement).all()
    
    def get_by_order_number(self, db: Session, order_number: str) -> Optional[Order]:
        statement = select(Order).where(Order.order_number == order_number)
        return db.exec(statement).first()
    
    def create(self, db: Session, order_in: OrderCreate, user_id: int) -> Order:
        db_order = Order(**order_in.dict(), user_id=user_id)
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
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