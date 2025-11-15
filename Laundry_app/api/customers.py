from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

from db.session import get_db
from schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate, CustomerLogin
from Laundry_app.crud.crud_user import crud_user
from core.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from core.config import settings
from schemas.address import AddressCreate, AddressUpdate, AddressResponse
from Laundry_app.crud.crud_address import crud_address

router = APIRouter()

#  CUSTOMER REGISTRATION (POST) - Public endpoint
@router.post("/register", response_model=CustomerResponse)
def register_customer(
    customer_data: CustomerCreate, 
    db: Session = Depends(get_db)
):
    # Check if customer already exists with same mobile number
    existing_mobile = crud_user.get_by_mobile(db, customer_data.mobile_no)
    if existing_mobile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number already registered"
        )
    
    # Check if email already exists (if provided)
    if customer_data.email:
        existing_email = crud_user.get_by_email(db, customer_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Hash the password
    hashed_password = get_password_hash(customer_data.password)
    
    image_url = customer_data.image_url or "/static/images/default-avatar.jpg"

    # Create customer data with role="customer"
    customer_dict = customer_data.dict()
    customer_dict["password"] = hashed_password
    customer_dict["role"] = "customer"  # Always set role as customer
    customer_dict["status"] = "active"
    customer_dict["image_url"] = image_url

    # Create the customer
    customer = crud_user.create(db, customer_dict)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )
    
    return customer

#  CUSTOMER LOGIN (POST) - Public endpoint
# @router.post("/login")
# def login_customer(
#     login_data: CustomerLogin, 
#     db: Session = Depends(get_db)
# ):
#     """
#     Customer login with name OR mobile number and password
#     """
#     customer = None
    
#     # Try to find customer by mobile number
#     if login_data.mobile_no:
#         customer = crud_user.get_by_mobile(db, login_data.mobile_no)
#     # If mobile not provided, try by name
#     elif login_data.name:
#         customer = crud_user.get_by_name(db, login_data.name)
    
#     # Check if customer exists and verify password
#     if not customer or not verify_password(login_data.password, customer.password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect credentials"
#         )
    
#     # Check if user is actually a customer
#     if customer.role != "customer":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access denied. Not a customer account."
#         )
    
#     # Check account status
#     if customer.status != "active":
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Account is inactive"
#         )
    
#     # Generate access token
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         subject=customer.user_id, 
#         expires_delta=access_token_expires
#     )
    
#     return {
#         "access_token": access_token,
#         "token_type": "bearer",
#         "customer": CustomerResponse.from_orm(customer)
#     }

#  GET ALL CUSTOMERS (GET) - Admin/Staff only
@router.get("/", response_model=List[CustomerResponse])
def get_customers(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Get all customers (Admin/Staff only)
    """
    from sqlmodel import select
    from models.user import User
    
    # Get only customers (role = 'customer')
    statement = select(User).where(User.role == "customer").offset(skip).limit(limit)
    customers = db.exec(statement).all()
    return customers

#  GET CUSTOMER BY ID (GET) - Admin/Staff or own profile
@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get customer by ID
    """
    customer = crud_user.get_by_id(db, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Check if the user is actually a customer
    if customer.role.lower()  != "customer":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int, 
    customer_data: CustomerUpdate, 
    db: Session = Depends(get_db)
):
    """Update customer profile"""
    try:
        # Get user by ID
        customer = crud_user.get_by_id(db, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Check if the user is actually a customer
        if customer.role.lower()  != "customer":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Validate status value
        valid_statuses = ['active', 'inactive', 'suspended']
        if customer_data.status and customer_data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status must be one of: {', '.join(valid_statuses)}"
            )
        
        # Update customer
        updated_customer = crud_user.update(db, customer_id, customer_data)
        if not updated_customer:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update customer"
            )
        
        return updated_customer
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during update"
        )
    
# #  UPDATE CUSTOMER (PUT) - Admin/Staff or own profile
# @router.put("/{customer_id}", response_model=CustomerResponse)
# def update_customer(
#     customer_id: int, 
#     customer_data: CustomerUpdate, 
#     db: Session = Depends(get_db)
# ):
#     """
#     Update customer profile
#     """
#     customer = crud_user.get_by_id(db, customer_id)
#     if not customer:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Customer not found"
#         )
    
#     # Check if the user is actually a customer
#     if customer.role != "customer":
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Customer not found"
#         )
    
#     # Update customer
#     updated_customer = crud_user.update(db, customer_id, customer_data)
#     return updated_customer

#  DELETE CUSTOMER (DELETE) - Admin/Staff only
@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int, 
    db: Session = Depends(get_db)
):
    """
    Delete customer (soft delete - set status to inactive)
    """
    customer = crud_user.get_by_id(db, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Check if the user is actually a customer
    if customer.role.lower()  != "customer":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Soft delete - set status to inactive
    customer.status = "inactive"
    db.add(customer)
    db.commit()
    
    return {"message": "Customer deleted successfully"}

# ============================================================================
# ADDRESS MANAGEMENT ENDPOINTS - Add these at the end of your file
# ============================================================================

#  ADD ADDRESS FOR CUSTOMER
@router.post("/{customer_id}/addresses", response_model=AddressResponse)
def create_customer_address(
    customer_id: int,
    address_data: AddressCreate,
    db: Session = Depends(get_db)
):
    """Create a new address for customer"""
    # Check if customer exists
    customer = crud_user.get_by_id(db, customer_id)
    if not customer or customer.role.lower()  != "customer":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Create address
    address_dict = address_data.dict()
    address_dict["user_id"] = customer_id
    
    address = crud_address.create(db, address_dict)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create address"
        )
    
    return address

#  GET ALL ADDRESSES OF CUSTOMER
@router.get("/{customer_id}/addresses", response_model=List[AddressResponse])
def get_customer_addresses(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get all addresses of a customer"""
    # Check if customer exists
    customer = crud_user.get_by_id(db, customer_id)
    if not customer or customer.role.lower() != "customer":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    addresses = crud_address.get_by_user_id(db, customer_id)
    return addresses

#  GET SPECIFIC ADDRESS
@router.get("/{customer_id}/addresses/{address_id}", response_model=AddressResponse)
def get_customer_address(
    customer_id: int,
    address_id: int,
    db: Session = Depends(get_db)
):
    """Get specific address of a customer"""
    address = crud_address.get_by_id(db, address_id)
    if not address or address.user_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    return address

#  UPDATE ADDRESS
@router.put("/{customer_id}/addresses/{address_id}", response_model=AddressResponse)
def update_customer_address(
    customer_id: int,
    address_id: int,
    address_data: AddressUpdate,
    db: Session = Depends(get_db)
):
    """Update customer address"""
    address = crud_address.get_by_id(db, address_id)
    if not address or address.user_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    updated_address = crud_address.update(db, address_id, address_data)
    if not updated_address:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update address"
        )
    
    return updated_address

#  DELETE ADDRESS
@router.delete("/{customer_id}/addresses/{address_id}")
def delete_customer_address(
    customer_id: int,
    address_id: int,
    db: Session = Depends(get_db)
):
    """Delete customer address (soft delete)"""
    address = crud_address.get_by_id(db, address_id)
    if not address or address.user_id != customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    success = crud_address.delete(db, address_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete address"
        )
    
    return {"message": "Address deleted successfully"}

#  GET DEFAULT ADDRESS
@router.get("/{customer_id}/addresses/default", response_model=AddressResponse)
def get_default_address(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get customer's default address"""
    print(f"DEBUG: Looking for customer {customer_id}")
    customer = crud_user.get_by_id(db, customer_id)
    if not customer or customer.role.lower() != "customer":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    default_address = crud_address.get_default_address(db, customer_id)
    print(f"DEBUG: Found address: {default_address}")
    
    if not default_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default address found"
        )
    
    return default_address