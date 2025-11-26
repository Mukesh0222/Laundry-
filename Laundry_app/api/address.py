from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from db.session import get_db
from models.address import Address
from schemas.address import AddressCreate, AddressResponse, AddressUpdate
from dependencies.auth import get_current_user
from models.user import User

router = APIRouter()

@router.post("/", response_model=AddressResponse)
def create_address(
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    #  Duplicate address validation
    existing = db.exec(
        select(Address).where(
            Address.user_id == current_user.user_id,
            Address.address_line1 == address.address_line1
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Address already exists")

    db_address = Address(**address.dict(), user_id=current_user.user_id)
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

@router.get("/", response_model=List[AddressResponse])
def read_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    statement = select(Address).where(Address.user_id == current_user.user_id)
    addresses = db.exec(statement).all()
    return addresses

# @router.get("/{address_id}", response_model=AddressResponse)
# def read_address(
#     address_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     address = db.get(Address, address_id)
#     if not address or address.user_id != current_user.user_id:
#         raise HTTPException(status_code=404, detail="Address not found")
#     return address

# @router.put("/{address_id}", response_model=AddressResponse)
# def update_address(
#     address_id: int,
#     address: AddressUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     db_address = db.get(Address, address_id)
#     if not db_address or db_address.user_id != current_user.user_id:
#         raise HTTPException(status_code=404, detail="Address not found")
    
#     for key, value in address.dict(exclude_unset=True).items():
#         setattr(db_address, key, value)
    
#     db.add(db_address)
#     db.commit()
#     db.refresh(db_address)
#     return db_address

# @router.delete("/{address_id}")
# def delete_address(
#     address_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     address = db.get(Address, address_id)
#     if not address or address.user_id != current_user.user_id:
#         raise HTTPException(status_code=404, detail="Address not found")
    
#     db.delete(address)
#     db.commit()
#     return {"message": "Address deleted successfully"}


# ==================== USER-SPECIFIC OPERATIONS ====================

@router.get("/user/{user_id}", response_model=List[AddressResponse])
def get_addresses_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all addresses by user ID"""
    try:
        print(f" Fetching addresses for user ID: {user_id}")
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Use db.query() instead of db.exec()
        addresses = db.query(Address).filter(Address.user_id == user_id).all()
        
        print(f" Found {len(addresses)} addresses for user {user_id}")
        return addresses
        
    except HTTPException:
        raise
    except Exception as e:
        print(f" Error fetching user addresses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch addresses: {str(e)}"
        )

@router.post("/user/{user_id}", response_model=AddressResponse)
def create_address_for_user(
    user_id: int,
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create address for specific user ID"""
    try:
        print(f" Creating address for user ID: {user_id}")
        print(f" Address data: {address.dict()}")
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Duplicate address validation using db.query()
        existing = db.query(Address).filter(
            Address.user_id == user_id,
            Address.address_line1 == address.address_line1
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Address already exists for this user")

        # Create address with specified user_id
        address_data = address.dict()
        address_data['user_id'] = user_id
        
        db_address = Address(**address_data)
        db.add(db_address)
        db.commit()
        db.refresh(db_address)
        
        print(f" Address created successfully: {db_address.address_id}")
        return db_address
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f" Error creating address: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create address: {str(e)}")

@router.get("/user/{user_id}/{address_id}", response_model=AddressResponse)
def get_address_by_user_and_id(
    user_id: int,
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific address by user ID and address ID"""
    try:
        print(f" Fetching address {address_id} for user {user_id}")
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        address = db.query(Address).filter(Address.address_id == address_id).first()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
            
        if address.user_id != user_id:
            raise HTTPException(status_code=404, detail="Address not found for this user")
        
        print(f" Found address: {address_id}")
        return address
        
    except HTTPException:
        raise
    except Exception as e:
        print(f" Error fetching address: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch address: {str(e)}")

@router.put("/user/{user_id}/{address_id}", response_model=AddressResponse)
def update_address_for_user(
    user_id: int,
    address_id: int,
    address: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update specific address for user ID"""
    try:
        print(f" Updating address {address_id} for user {user_id}")
        print(f" Update data: {address.dict(exclude_unset=True)}")
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db_address = db.query(Address).filter(Address.address_id == address_id).first()
        if not db_address:
            raise HTTPException(status_code=404, detail="Address not found")
            
        if db_address.user_id != user_id:
            raise HTTPException(status_code=404, detail="Address not found for this user")
        
        # Update only provided fields
        update_data = address.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_address, key, value)
        
        db.add(db_address)
        db.commit()
        db.refresh(db_address)
        
        print(f" Address updated successfully: {address_id}")
        return db_address
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f" Error updating address: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update address: {str(e)}")

@router.delete("/user/{user_id}/{address_id}")
def delete_address_for_user(
    user_id: int,
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete specific address for user ID"""
    try:
        print(f" Deleting address {address_id} for user {user_id}")
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        address = db.query(Address).filter(Address.address_id == address_id).first()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
            
        if address.user_id != user_id:
            raise HTTPException(status_code=404, detail="Address not found for this user")
        
        db.delete(address)
        db.commit()
        
        print(f" Address deleted successfully: {address_id}")
        return {"message": "Address deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f" Error deleting address: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete address: {str(e)}")

# ==================== BULK OPERATIONS FOR USER ====================

@router.post("/user/{user_id}/bulk", response_model=List[AddressResponse])
def create_bulk_addresses_for_user(
    user_id: int,
    addresses: List[AddressCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple addresses for specific user ID"""
    try:
        print(f" Creating {len(addresses)} addresses for user: {user_id}")
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        created_addresses = []
        for address in addresses:
            # Check for duplicates using db.query()
            existing = db.query(Address).filter(
                Address.user_id == user_id,
                Address.address_line1 == address.address_line1
            ).first()

            if existing:
                continue  # Skip duplicates

            # Create address
            address_data = address.dict()
            address_data['user_id'] = user_id
            
            db_address = Address(**address_data)
            db.add(db_address)
            created_addresses.append(db_address)
        
        db.commit()
        
        # Refresh all created addresses
        for address in created_addresses:
            db.refresh(address)
        
        print(f" Created {len(created_addresses)} addresses for user {user_id}")
        return created_addresses
        
    except Exception as e:
        db.rollback()
        print(f" Error creating bulk addresses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create addresses: {str(e)}")

@router.delete("/user/{user_id}/all")
def delete_all_addresses_for_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete all addresses for specific user ID"""
    try:
        print(f" Deleting all addresses for user: {user_id}")
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Use db.query() instead of db.exec()
        addresses = db.query(Address).filter(Address.user_id == user_id).all()
        
        for address in addresses:
            db.delete(address)
        
        db.commit()
        
        print(f" Deleted {len(addresses)} addresses for user {user_id}")
        return {"message": f"Deleted {len(addresses)} addresses successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f" Error deleting all addresses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete addresses: {str(e)}")

# ==================== CURRENT USER OPERATIONS (Optional) ====================

# @router.get("/me", response_model=List[AddressResponse])
# def get_my_addresses(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Get current user's addresses (convenience endpoint)"""
#     return get_addresses_by_user_id(current_user.user_id, db, current_user)

# @router.post("/me", response_model=AddressResponse)
# def create_my_address(
#     address: AddressCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """Create address for current user (convenience endpoint)"""
#     return create_address_for_user(current_user.user_id, address, db, current_user)