from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
import random
import string
from datetime import datetime

from db.session import get_db
from models.order import Order, OrderStatus, ServiceType
from models.order_item import OrderItem
from schemas.order import OrderCreate, OrderResponse, OrderUpdate
from dependencies.auth import get_current_user
from models.user import User
import test_order as test_order

router = APIRouter()

def generate_Token_no():
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD{date_str}-{random_str}"
    
# print(" Order router loaded successfully")

def calculate_order_total(items: List) -> float:
    """Calculate total order amount"""
    return sum(item.quantity * item.unit_price for item in items)


# @router.post("/", response_model=OrderResponse)
# def create_order(
#     order: OrderCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         print(f" Creating order for user: {current_user.user_id}, Name: {current_user.name}")
        
#         # If address_id is 0, create a default address
#         if order.address_id == 0:
#             from models.address import Address
#             # Create a default address for the user
#             default_address = Address(
#                 user_id=current_user.user_id,
#                 address_line1="Default Address",
#                 city="Default City",
#                 state="Default State",
#                 pincode="000000",
#                 is_default=True
#             )
#             db.add(default_address)
#             db.commit()
#             db.refresh(default_address)
#             order.address_id = default_address.address_id
#             print(f" Created default address: {default_address.address_id}")
        
#         # Verify address belongs to user
#         from models.address import Address
#         address = db.get(Address, order.address_id)
#         if not address:
#             raise HTTPException(status_code=400, detail="Address not found")
        
#         if address.user_id != current_user.user_id:
#             raise HTTPException(status_code=400, detail="Invalid address")
        
#         # Create order
#         db_order = Order(
#             user_id=current_user.user_id,
#             address_id=order.address_id,
#             order_number=generate_order_number(),
#             service=order.service,
#             status=OrderStatus.PENDING
#         )
#         db.add(db_order)
#         db.commit()
#         db.refresh(db_order)
        
#         print(f" Order created: {db_order.order_number}")
        
#         # Create order items
#         for item in order.items:
#             db_item = OrderItem(
#                 order_id=db_order.order_id,
#                 category_name=item.category_name,
#                 product_name=item.product_name,
#                 quantity=item.quantity,
#                 service=order.service,
#                 # unit_price=10.0  #  Add default unit_price
#             )
#             db.add(db_item)
        
#         db.commit()
#         db.refresh(db_order)
#         return db_order
        
#     except Exception as e:
#         db.rollback()
#         print(f" Order creation error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")

@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        print(f" Creating order for user: {current_user.user_id}, Name: {current_user.name}")
        print(f" Request data: {order.dict()}")

        print(f"Available fields in order: {order.dict().keys()}")
        # Validate order items
        for index, item in enumerate(order.items):
            if not item.category_name or item.category_name.strip() == "":
                raise HTTPException(
                    status_code=400, 
                    detail=f"Item {index+1}: Category name is required"
                )
            if not item.product_name or item.product_name.strip() == "":
                raise HTTPException(
                    status_code=400, 
                    detail=f"Item {index+1}: Product name is required"
                )

        from models.address import Address
        
        #  STEP 1: Always create a NEW address (don't use existing address_id)
        new_address = Address(
            user_id=current_user.user_id,
            name=current_user.name,
            mobile_no=current_user.mobile_no,
            address_line1=order.address_line1.strip(),
            address_line2=order.address_line2.strip() if order.address_line2 else "",
            city=order.city.strip(),
            state=order.state.strip(),
            pincode=order.pincode.strip(),
            landmark=order.landmark.strip() if order.landmark else ""
        )
        db.add(new_address)
        db.commit()
        db.refresh(new_address)
        
        print(f" New address created with ID: {new_address.address_id}")
        
        #  STEP 2: Create order with the NEW address
        db_order = Order(
            user_id=current_user.user_id,
            address_id=new_address.address_id,
            Token_no=generate_Token_no(),
            service=order.service,
            status=OrderStatus.PENDING
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        print(f" Order created: {db_order.Token_no}")
        
        #  STEP 3: Create order items
        created_items = [] 
        for item in order.items:
            db_item = OrderItem(
                order_id=db_order.order_id,
                category_name=item.category_name,
                product_name=item.product_name,
                quantity=item.quantity,
                service=order.service,
                unit_price=10.0
            )
            db.add(db_item)
            created_items.append(db_item)
        
        db.commit()
        # db.refresh(db_order)

        # STEP 4: Refresh items to get their IDs
        for item in created_items:
            db.refresh(item)
        
        # STEP 5: Create items response
        items_response = []
        for item in created_items:
            items_response.append({
                "order_item_id": item.order_item_id,
                "order_id": item.order_id,
                "category_name": item.category_name,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "service": item.service,
                "status": item.status,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "created_by": item.created_by,
                "updated_by": item.updated_by
            })
        
        # MANUALLY CREATE RESPONSE WITH REQUEST DATA
        response_data = {
            "order_id": db_order.order_id,
            "user_id": db_order.user_id,
            "address_id": db_order.address_id,
            "Token_no": db_order.Token_no,
            "service": db_order.service,
            "status": db_order.status,
            "created_at": db_order.created_at,
            "updated_at": db_order.updated_at,
            "created_by": db_order.created_by,
            "updated_by": db_order.updated_by,
            # Use address data from REQUEST (not database defaults)
            "address_line1": order.address_line1,
            "address_line2": order.address_line2,
            "city": order.city,
            "state": order.state,
            "pincode": order.pincode,
            "landmark": order.landmark,
            "order_items": items_response,
            "items": items_response,
            "address_details": {
                "address_line1": new_address.address_line1,
                "address_line2": new_address.address_line2,
                "city": new_address.city,
                "state": new_address.state,
                "pincode": new_address.pincode,
                # "landmark": new_address.landmark
            }
        }
        
        print(" Order creation completed successfully!")
        print(f" Response items count: {len(items_response)}")
        return OrderResponse(**response_data)
        
    except Exception as e:
        db.rollback()
        print(f" Order creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")

@router.get("/", response_model=List[OrderResponse])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    service: Optional[ServiceType] = None,  # Service filter
    status: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role in ["staff", "admin"]:
        statement = select(Order).offset(skip).limit(limit)
    else:
        statement = select(Order).where(Order.user_id == current_user.user_id).offset(skip).limit(limit)
    
     # Apply filters
    if service:
        statement = statement.where(Order.service == service)
    if status:
        statement = statement.where(Order.status == status)

    orders = db.exec(statement).all()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(f" Checking order {order_id} for user {current_user.user_id} (Role: {current_user.role})")
    
    order = db.get(Order, order_id)
    
    if not order:
        print(f" Order {order_id} not found")
        raise HTTPException(status_code=404, detail="Order not found")
    
    print(f" Order found - User ID: {order.user_id}, Current User ID: {current_user.user_id}")
    
    # Check permissions
    if current_user.role.lower() not in ["staff", "admin"] and order.user_id != current_user.user_id:
        print(f" Permission denied - Order belongs to user {order.user_id}, but current user is {current_user.user_id}")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    print(f" Access granted to order {order_id}")
    return order

@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Only staff/admin can update order status
    if current_user.role not in ["staff", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # for key, value in order_update.dict(exclude_unset=True).items():
    #     setattr(order, key, value)
    
    # Update fields
    update_data = order_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)
    
    order.updated_at = datetime.utcnow()
    order.updated_by = current_user.email

    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if current_user.role not in ["staff", "admin"] and order.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(order)
    db.commit()
    return {"message": "Order deleted successfully"}


