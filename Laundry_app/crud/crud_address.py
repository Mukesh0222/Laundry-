# from sqlmodel import Session, select
# from typing import List, Optional
# from models.address import Address
# from schemas.address import AddressCreate, AddressUpdate

# class CRUDAddress:
#     def get_by_id(self, db: Session, address_id: int) -> Optional[Address]:
#         return db.get(Address, address_id)
    
#     def get_by_user(self, db: Session, user_id: int) -> List[Address]:
#         statement = select(Address).where(Address.user_id == user_id)
#         return db.exec(statement).all()
    
#     def create(self, db: Session, address_in: AddressCreate, user_id: int) -> Address:
#         db_address = Address(**address_in.dict(), user_id=user_id)
#         db.add(db_address)
#         db.commit()
#         db.refresh(db_address)
#         return db_address
    
#     def update(self, db: Session, address_id: int, address_in: AddressUpdate) -> Optional[Address]:
#         address = self.get_by_id(db, address_id)
#         if address:
#             update_data = address_in.dict(exclude_unset=True)
#             for field, value in update_data.items():
#                 setattr(address, field, value)
#             db.add(address)
#             db.commit()
#             db.refresh(address)
#         return address
    
#     def delete(self, db: Session, address_id: int) -> bool:
#         address = self.get_by_id(db, address_id)
#         if address:
#             db.delete(address)
#             db.commit()
#             return True
#         return False

# crud_address = CRUDAddress()

from sqlmodel import Session, select
from models.address import Address
from typing import List, Optional

class CRUDAddress:
    def get_by_id(self, db: Session, address_id: int) -> Optional[Address]:
        statement = select(Address).where(Address.address_id == address_id)
        return db.exec(statement).first()
    
    def get_by_user_id(self, db: Session, user_id: int) -> List[Address]:
        statement = select(Address).where(
            Address.user_id == user_id,
            # Address.status == "active"
        )
        return db.exec(statement).all()
    
    def get_default_address(self, db: Session, user_id: int) -> Optional[Address]:
        statement = select(Address).where(
            Address.user_id == user_id,
            # Address.is_default == True,
            # Address.status == "active"
        )
        return db.exec(statement).first()
    
    def create(self, db: Session, address_data: dict) -> Optional[Address]:
        try:
            # If this is set as default, remove default from other addresses
            if address_data.get('is_default'):
                self.remove_default_from_others(db, address_data['user_id'])
            
            db_address = Address(
            user_id=address_data['user_id'],
            # address_type=address_data.get('address_type', 'home'),
            name=address_data['name'],
            mobile_no=address_data['mobile_no'],
            address_line1=address_data['address_line1'],
            address_line2=address_data.get('address_line2'),
            landmark=address_data.get('landmark'),
            city=address_data['city'],
            state=address_data['state'],
            postal_code=address_data['postal_code'],
            is_default=address_data.get('is_default', False),
            # status=address_data.get('status', 'active')
            )
            db.add(db_address)
            db.commit()
            db.refresh(db_address)
            return db_address
        except Exception as e:
            db.rollback()
            print(f"Error creating address: {e}")
            return None
    
    def update(self, db: Session, address_id: int, address_data) -> Optional[Address]:
        address = self.get_by_id(db, address_id)
        if not address:
            return None
        
        update_data = address_data.dict(exclude_unset=True)
        
        # If setting as default, remove default from others
        if update_data.get('is_default'):
            self.remove_default_from_others(db, address.user_id)
        
        for field, value in update_data.items():
            setattr(address, field, value)
        
        db.add(address)
        db.commit()
        db.refresh(address)
        return address
    
    def remove_default_from_others(self, db: Session, user_id: int):
        """Remove default flag from all other addresses of the user"""
        statement = select(Address).where(
            Address.user_id == user_id,
            # Address.is_default == True
        )
        default_addresses = db.exec(statement).all()
        
        for addr in default_addresses:
            addr.is_default = False
            db.add(addr)
    
    def delete(self, db: Session, address_id: int) -> bool:
        """Soft delete address"""
        address = self.get_by_id(db, address_id)
        if not address:
            return False
        
        address.status = "inactive"
        db.add(address)
        db.commit()
        return True

# Create instance
crud_address = CRUDAddress()