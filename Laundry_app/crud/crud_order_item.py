from sqlmodel import Session, select
from typing import List, Optional
from models.order_item import OrderItem, ServiceType
from schemas.order_item import OrderItemCreate, OrderItemUpdate

class CRUDOrderItem:
    def get_by_id(self, db: Session, order_item_id: int) -> Optional[OrderItem]:
        return db.get(OrderItem, order_item_id)
    
    def get_by_order(self, db: Session, order_id: int) -> List[OrderItem]:
        statement = select(OrderItem).where(OrderItem.order_id == order_id)
        return db.exec(statement).all()
    
    def get_by_service(self, db: Session, service: ServiceType) -> List[OrderItem]:
        statement = select(OrderItem).where(OrderItem.service == service)
        return db.exec(statement).all()
    
    def create(self, db: Session, order_item_in: OrderItemCreate, order_id: int) -> OrderItem:
        db_item = OrderItem(**order_item_in.dict(), order_id=order_id)
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    def create_bulk(self, db: Session, items: List[OrderItemCreate], order_id: int) -> List[OrderItem]:
        db_items = []
        for item in items:
            db_item = OrderItem(**item.dict(), order_id=order_id)
            db.add(db_item)
            db_items.append(db_item)
        db.commit()
        for item in db_items:
            db.refresh(item)
        return db_items
    
    def update(self, db: Session, order_item_id: int, order_item_in: OrderItemUpdate) -> Optional[OrderItem]:
        item = self.get_by_id(db, order_item_id)
        if item:
            update_data = order_item_in.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(item, field, value)
            db.add(item)
            db.commit()
            db.refresh(item)
        return item
    
    def delete(self, db: Session, order_item_id: int) -> bool:
        item = self.get_by_id(db, order_item_id)
        if item:
            db.delete(item)
            db.commit()
            return True
        return False

crud_order_item = CRUDOrderItem()