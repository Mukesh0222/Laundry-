from sqlmodel import Session, select
from typing import List, Optional
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.pickup_delivery import PickupDelivery, ServiceType
from Laundry_app.crud.crud_order import crud_order
from Laundry_app.crud.crud_order_item import crud_order_item
from Laundry_app.crud.crud_pickup_delivery import crud_pickup_delivery
from datetime import datetime, timedelta
from models.order_archive import OrderArchive, OrderItemsArchive, DeletionReason
from models.user import User
import json

class OrderService:
    def create_complete_order(
        self, 
        db: Session, 
        user_id: int, 
        address_id: int, 
        items: List[dict],
        pickup_date: datetime
    ) -> Order:
        
        order_data = {
            "address_id": address_id,
            "items": items
        }
        
        
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

   
    @staticmethod
    def delete_order_with_archive(
        db: Session,
        order_id: int,
        deletion_reason: DeletionReason,
        deleted_by: User,
        notes: Optional[str] = None
    ):
        """
        Soft delete order by moving to archive and then deleting from main tables
        """
        # Get the order with items
        order = db.get(Order, order_id)
        if not order:
            raise ValueError("Order not found")
        
        # Get all order items
        order_items = db.exec(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).all()
        
        # Create archive record
        archive_order = OrderArchive(
            original_order_id=order_id,
            user_id=order.user_id,
            order_data=order.dict(),  # Store complete order data
            order_items_data={
                "items": [item.dict() for item in order_items],
                "total_items": len(order_items),
                "total_amount": order.total_amount
            },
            deletion_reason=deletion_reason,
            deleted_by=deleted_by.user_id,
            deleted_by_role=deleted_by.role,
            notes=notes
        )
        
        db.add(archive_order)
        db.flush()  # Get the archive ID without committing
        
        # Archive individual items
        for item in order_items:
            archive_item = OrderItemsArchive(
                original_item_id=item.id,
                original_order_id=order_id,
                archive_order_id=archive_order.id,
                item_data=item.dict()
            )
            db.add(archive_item)
        
        # Delete from main tables
        for item in order_items:
            db.delete(item)
        
        db.delete(order)
        db.commit()
        
        return archive_order
    
    @staticmethod
    def get_archived_orders(
        db: Session,
        original_order_id: Optional[int] = None,
        user_id: Optional[int] = None,
        deletion_reason: Optional[DeletionReason] = None,
        deleted_by: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ):
        """Get archived orders with filters"""
        query = select(OrderArchive)
        
        if original_order_id:
            query = query.where(OrderArchive.original_order_id == original_order_id)
        if user_id:
            query = query.where(OrderArchive.user_id == user_id)
        if deletion_reason:
            query = query.where(OrderArchive.deletion_reason == deletion_reason)
        if deleted_by:
            query = query.where(OrderArchive.deleted_by == deleted_by)
        if date_from:
            query = query.where(OrderArchive.deleted_at >= date_from)
        if date_to:
            query = query.where(OrderArchive.deleted_at <= date_to)
            
        query = query.offset(skip).limit(limit).order_by(OrderArchive.deleted_at.desc())
        
        return db.exec(query).all()
    
    @staticmethod
    def restore_order_from_archive(db: Session, archive_id: int):
        """Restore an order from archive (admin only)"""
        archived_order = db.get(OrderArchive, archive_id)
        if not archived_order:
            raise ValueError("Archived order not found")
        
        # Check if original order ID still exists
        existing_order = db.get(Order, archived_order.original_order_id)
        if existing_order:
            raise ValueError("Original order ID already exists in active orders")
        
        # Restore order
        order_data = archived_order.order_data
        order = Order(**order_data)
        db.add(order)
        db.flush()
        
        # Restore order items
        archived_items = db.exec(
            select(OrderItemsArchive).where(
                OrderItemsArchive.archive_order_id == archive_id
            )
        ).all()
        
        for archived_item in archived_items:
            item_data = archived_item.item_data
            item_data['order_id'] = order.id  # Update with new order ID
            order_item = OrderItem(**item_data)
            db.add(order_item)
        
        # Delete from archive
        for archived_item in archived_items:
            db.delete(archived_item)
        db.delete(archived_order)
        
        db.commit()
        return order
    
order_service = OrderService()