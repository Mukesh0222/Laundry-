from sqlmodel import Session, select
from typing import List, Optional
from models.pickup_delivery import PickupDelivery, ServiceStatus, ServiceType
from schemas.pickup_delivery import PickupDeliveryCreate, PickupDeliveryUpdate, PickupDeliveryResponse
from datetime import datetime

class CRUDPickupDelivery:
    def get_by_id(self, db: Session, pd_id: int) -> Optional[PickupDelivery]:
        return db.get(PickupDelivery, pd_id)
    
    def get_by_order(self, db: Session, order_id: int) -> List[PickupDelivery]:
        statement = select(PickupDelivery).where(PickupDelivery.order_id == order_id)
        return db.exec(statement).all()
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[PickupDelivery]:
        statement = select(PickupDelivery).offset(skip).limit(limit)
        return db.exec(statement).all()
    
    def get_by_type(self, db: Session, service_type: str, skip: int = 0, limit: int = 100) -> List[PickupDelivery]:
        statement = select(PickupDelivery).where(PickupDelivery.type == service_type).offset(skip).limit(limit)
        return db.exec(statement).all()
    
    def create(self, db: Session, pd_in: PickupDeliveryCreate) -> PickupDelivery:
        db_pd = PickupDelivery(**pd_in.dict())
        db.add(db_pd)
        db.commit()
        db.refresh(db_pd)
        return db_pd
    
    # def update(self, db: Session, pd_id: int, pd_in: PickupDeliveryUpdate) -> Optional[PickupDelivery]:
    #     pd = self.get_by_id(db, pd_id)
    #     if pd:
    #         update_data = pd_in.dict(exclude_unset=True)
    #         for field, value in update_data.items():
    #             setattr(pd, field, value)
    #         db.add(pd)
    #         db.commit()
    #         db.refresh(pd)
    #     return pd
    
    def update(self, db: Session, pd_id: int, pd_in: PickupDeliveryUpdate) -> Optional[PickupDelivery]:
        pd = self.get_by_id(db, pd_id)
        if pd:
            update_data = pd_in.dict(exclude_unset=True)
            
            
            if 'status' in update_data:
                new_status = update_data['status']
                if new_status == ServiceStatus.IN_PROGRESS and not pd.pickup_at:
                    update_data['pickup_at'] = datetime.utcnow()
                elif new_status == ServiceStatus.COMPLETED:
                    if pd.service_type == ServiceType.PICKUP and not pd.picked_at:
                        update_data['picked_at'] = datetime.utcnow()
                    elif pd.service_type == ServiceType.DELIVERY and not pd.delivered_at:
                        update_data['delivered_at'] = datetime.utcnow()
                    update_data['actual_date'] = datetime.utcnow()
            
            for field, value in update_data.items():
                setattr(pd, field, value)
            
            pd.pickup_update_at = datetime.utcnow()  
            db.add(pd)
            db.commit()
            db.refresh(pd)
        return pd

    def mark_picked_up(self, db: Session, pickup_id: int) -> Optional[PickupDelivery]:
        """Mark as picked up with timestamp"""
        pickup = self.get_by_id(db, pickup_id)
        if pickup and pickup.service_type == ServiceType.PICKUP:
            pickup.picked_at = datetime.utcnow()
            pickup.status = ServiceStatus.COMPLETED
            pickup.actual_date = datetime.utcnow()
            pickup.pickup_update_at = datetime.utcnow()
            db.add(pickup)
            db.commit()
            db.refresh(pickup)
        return pickup

    def mark_delivered(self, db: Session, delivery_id: int) -> Optional[PickupDelivery]:
        """Mark as delivered with timestamp"""
        delivery = self.get_by_id(db, delivery_id)
        if delivery and delivery.service_type == ServiceType.DELIVERY:
            delivery.delivered_at = datetime.utcnow()
            delivery.status = ServiceStatus.COMPLETED
            delivery.actual_date = datetime.utcnow()
            delivery.pickup_update_at = datetime.utcnow()
            db.add(delivery)
            db.commit()
            db.refresh(delivery)
        return delivery

    def delete(self, db: Session, pd_id: int) -> bool:
        pd = self.get_by_id(db, pd_id)
        if pd:
            db.delete(pd)
            db.commit()
            return True
        return False

crud_pickup_delivery = CRUDPickupDelivery()