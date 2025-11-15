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

@router.get("/{address_id}", response_model=AddressResponse)
def read_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    address = db.get(Address, address_id)
    if not address or address.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Address not found")
    return address

@router.put("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_address = db.get(Address, address_id)
    if not db_address or db_address.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Address not found")
    
    for key, value in address.dict(exclude_unset=True).items():
        setattr(db_address, key, value)
    
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address

@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    address = db.get(Address, address_id)
    if not address or address.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Address not found")
    
    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}