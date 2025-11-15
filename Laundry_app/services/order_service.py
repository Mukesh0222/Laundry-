from sqlmodel import Session
from typing import List, Optional
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.pickup_delivery import PickupDelivery, ServiceType
from Laundry_app.crud.crud_order import crud_order
from Laundry_app.crud.crud_order_item import crud_order_item
from Laundry_app.crud.crud_pickup_delivery import crud_pickup_delivery
from datetime import datetime, timedelta

class OrderService:
    def create_complete_order(
        self, 
        db: Session, 
        user_id: int, 
        address_id: int, 
        items: List[dict],
        pickup_date: datetime
    ) -> Order:
        # Create order
        order_data = {
            "address_id": address_id,
            "items": items
        }
        
        # This would integrate with the existing order creation logic
        # For now, using simplified version
        order = crud_order.create(db, order_data, user_id)
        
        # Schedule pickup
        pickup_data = {
            "order_id": order.order_id,
            "type": ServiceType.PICKUP,
            "scheduled_date": pickup_date
        }
        crud_pickup_delivery.create(db, pickup_data)
        
        return order
    
    def get_user_orders_with_details(self, db: Session, user_id: int) -> List[Order]:
        orders = crud_order.get_by_user(db, user_id)
        # Add order items and pickup/delivery info to each order
        for order in orders:
            order.order_items = crud_order_item.get_by_order(db, order.order_id)
            order.pickups_deliveries = crud_pickup_delivery.get_by_order(db, order.order_id)
        return orders
    
    def update_order_status(self, db: Session, order_id: int, new_status: OrderStatus) -> Optional[Order]:
        order = crud_order.get_by_id(db, order_id)
        if order:
            order.status = new_status
            order.updated_at = datetime.utcnow()
            db.add(order)
            db.commit()
            db.refresh(order)
        return order
    
    def schedule_delivery(self, db: Session, order_id: int, delivery_date: datetime) -> Optional[PickupDelivery]:
        delivery_data = {
            "order_id": order_id,
            "type": ServiceType.DELIVERY,
            "scheduled_date": delivery_date
        }
        return crud_pickup_delivery.create(db, delivery_data)

order_service = OrderService()