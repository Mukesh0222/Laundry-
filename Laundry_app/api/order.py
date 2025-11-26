from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
import random
import string
from datetime import datetime

from db.session import get_db
from models.order import Order, OrderStatus, ServiceType
from models.order_item import OrderItem
from schemas.order import OrderCreate, OrderResponse, OrderUpdate, UserOrdersResponse
from dependencies.auth import get_current_user, get_or_create_guest_user
from models.user import User
from models.address import Address
# from models.address import Address
import test_order as test_order

router = APIRouter()

def generate_Token_no():
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD{date_str}-{random_str}"
    

def calculate_order_total(items: List) -> float:
    """Calculate total order amount"""
    return sum(item.quantity * item.unit_price for item in items)

# def get_user_identifier(user: User) -> str:
#     """Get user identifier (mobile_no) for created_by/updated_by fields"""
#     return user.mobile_no or user.name or "Unknown"

def get_created_by_identifier(current_user: User, order_data: OrderCreate) -> str:
    """Get created_by identifier - always use customer details"""
    
    print(f"🔍 DEBUG get_created_by_identifier:")
    print(f"   - Current User: {current_user.name} (Role: {current_user.role})")
    print(f"   - Order Customer Name: '{getattr(order_data, 'customer_name', 'NOT_FOUND')}'")
    print(f"   - Order Customer Mobile: '{getattr(order_data, 'customer_mobile', 'NOT_FOUND')}'")
    print(f"   - All order data keys: {order_data.dict().keys()}")
    
    # Check if customer_name and customer_mobile exist in request
    customer_name = getattr(order_data, 'customer_name', None)
    customer_mobile = getattr(order_data, 'customer_mobile', None)
    
    has_customer_details = (
        customer_name and 
        customer_name.strip() and 
        customer_mobile and 
        customer_mobile.strip()
    )
    
    print(f"🔍 Has customer details: {has_customer_details}")
    
    if current_user.role in ["admin", "staff"] and has_customer_details:
        result = f"Customer: {customer_name.strip()} ({customer_mobile.strip()})"
        print(f"✅ Using customer details: {result}")
        return result
    else:
        result = f"Customer: {current_user.name} ({current_user.mobile_no})"
        print(f"ℹ️ Using current user details: {result}")
        return result

@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        print(f" Creating order for user: {current_user.user_id}, Name: {current_user.name}")
        print(f" Request data: {order.dict()}")

        print(f" Current user: {current_user.name} (Role: {current_user.role})")
        print(f" Order customer details: {order.customer_name}, {order.customer_mobile}")

        created_by_identifier = get_created_by_identifier(current_user, order)
        print(f" Created_by identifier: {created_by_identifier}")

        # user_identifier = get_user_identifier(current_user)
        # print(f" User identifier for created_by: {user_identifier}")

        print(f"Available fields in order: {order.dict().keys()}")
        
        
        print(f" Order service from request: {getattr(order, 'service', 'NOT_PROVIDED')}")
        for i, item in enumerate(order.items):
            print(f" Item {i+1} service: {item.service}")

        
        if not hasattr(order, 'service') or not order.service:
            services = [item.service for item in order.items]
            main_service = max(set(services), key=services.count)
            order.service = main_service
            print(f" Derived main service from items: {main_service}")

        
        target_user = current_user  
        # initial_status = "pending"
       
        if current_user.role in ["admin", "staff"]:
            initial_status = "confirmed"
            print(f" Admin/Staff creating order - Status: {initial_status}")
            
            if order.customer_mobile and order.customer_mobile.strip():
                print(f" Admin creating order for customer: {order.customer_name} ({order.customer_mobile})")
                
                customer_user = db.query(User).filter(
                    User.mobile_no == order.customer_mobile
                ).first()
            
                if customer_user:
                    target_user = customer_user
                    print(f" Found existing customer: {customer_user.name} (ID: {customer_user.user_id})")
                else: 
                    new_customer_user = User(
                        name=order.customer_name,
                        mobile_no=order.customer_mobile,
                        email=f"guest_{order.customer_mobile}@laundryapp.com",  
                        password="guest_password",  
                        role="customer",
                        status="active",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_customer_user)
                    db.commit()
                    db.refresh(new_customer_user)
                    target_user = new_customer_user
                    print(f" Created new customer: {new_customer_user.name} (ID: {new_customer_user.user_id})")
            else:
                print(f" Admin creating order for themselves")
                target_user = current_user
        else:
            initial_status = "pending" 
            print(f" Customer creating own order - Status: {initial_status}")
        
        print(f" Final customer: {target_user.name} (ID: {target_user.user_id})")
        print(f" Initial order status: {initial_status}")
        
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
        
        new_address = Address(
            user_id=target_user.user_id, 
            name=order.customer_name or target_user.name,
            mobile_no=order.customer_mobile or target_user.mobile_no,
            address_line1=order.address_line1.strip(),
            address_line2=order.address_line2.strip() if order.address_line2 else "",
            city=order.city.strip(),
            state=order.state.strip(),
            pincode=order.pincode.strip(),
            # landmark=order.landmark.strip() if order.landmark else ""
        )
        db.add(new_address)
        db.commit()
        db.refresh(new_address)
        
        print(f" New address created with ID: {new_address.address_id}")
        
        db_order = Order(
            user_id=target_user.user_id, 
            address_id=new_address.address_id,
            Token_no=generate_Token_no(),
            service=order.service,
            status=initial_status,
            created_by=created_by_identifier,  
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        print(f" Order created: {db_order.Token_no}")
        
        created_items = [] 
        for item in order.items:
            item_status = "pending"
            if initial_status == "confirmed":
                item_status = "confirmed"
            db_item = OrderItem(
                order_id=db_order.order_id,
                category_name=item.category_name,
                product_name=item.product_name,
                quantity=item.quantity,
                service=item.service,
                unit_price=10.0,
                status=item_status,
                created_by=created_by_identifier,  
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(db_item)
            created_items.append(db_item)
        
        db.commit()
        # db.refresh(db_order)
 
        for item in created_items:
            db.refresh(item)
        
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
        
        
        response_data = {
            "order_id": db_order.order_id,
            "user_id": target_user.user_id, 
            "address_id": db_order.address_id,
            "Token_no": db_order.Token_no,
            "service": db_order.service,
            "status": db_order.status,
            "created_at": db_order.created_at,
            "updated_at": db_order.updated_at,
            "created_by": db_order.created_by,
            "updated_by": db_order.updated_by,
        
            "user_name": target_user.name,
            "user_mobile": target_user.mobile_no,
            "address_line1": order.address_line1,
            "address_line2": order.address_line2,
            "city": order.city,
            "state": order.state,
            "pincode": order.pincode,
            # "landmark": order.landmark,
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
        print(f" Item Services: {[item.service for item in created_items]}")
        return OrderResponse(**response_data)
        
    except Exception as e:
        db.rollback()
        print(f" Order creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")

# # @router.get("/", response_model=List[OrderResponse])
# # def read_orders(
# #     skip: int = 0,
# #     limit: int = 100,
# #     service: Optional[ServiceType] = None,  # Service filter
# #     status: Optional[OrderStatus] = None,
# #     db: Session = Depends(get_db),
# #     current_user: User = Depends(get_current_user)
# # ):
# #     if current_user.role in ["staff", "admin"]:
# #         statement = select(Order).offset(skip).limit(limit)
# #     else:
# #         statement = select(Order).where(Order.user_id == current_user.user_id).offset(skip).limit(limit)
    
# #      # Apply filters
# #     if service:
# #         statement = statement.where(Order.service == service)
# #     if status:
# #         statement = statement.where(Order.status == status)

# #     orders = db.exec(statement).all()
# #     return orders

# @router.get("/", response_model=List[OrderResponse])
# def read_orders(
#     skip: int = 0,
#     limit: int = 100,
#     service: Optional[ServiceType] = None,
#     status: Optional[OrderStatus] = None,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         print(f"Fetching orders for user: {current_user.user_id}, Role: {current_user.role}")
        
#         # Build query
#         if current_user.role in ["staff", "admin"]:
#             query = db.query(Order)
#         else:
#             query = db.query(Order).filter(Order.user_id == current_user.user_id)
        
#         # Apply filters
#         if service:
#             query = query.filter(Order.service == service)
#         if status:
#             query = query.filter(Order.status == status)
            
#         # Apply pagination and execute
#         orders = query.offset(skip).limit(limit).all()
        
#         print(f"Found {len(orders)} orders")
        
#         # Build response manually
#         response_orders = []
#         for order in orders:
#             # Load order items
#             order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
            
#             # Convert OrderItem objects to dictionaries
#             order_items_dicts = []
#             for item in order_items:
#                 order_items_dicts.append({
#                     "order_item_id": item.order_item_id,
#                     "order_id": item.order_id,
#                     "category_name": item.category_name,
#                     "product_name": item.product_name,
#                     "quantity": item.quantity,
#                     "service": item.service,
#                     "status": item.status,
#                     "created_at": item.created_at,
#                     "updated_at": item.updated_at,
#                     "created_by": item.created_by,
#                     "updated_by": item.updated_by
#                 })
            
#             # Load address and user
#             address = db.query(Address).filter(Address.address_id == order.address_id).first()
#             user = db.query(User).filter(User.user_id == order.user_id).first()

#             order_data = {
#                 "order_id": order.order_id,
#                 "user_id": order.user_id,
#                 "address_id": order.address_id,
#                 "Token_no": order.Token_no,
#                 "service": order.service,
#                 "status": order.status,
#                 "created_at": order.created_at,
#                 "updated_at": order.updated_at,
#                 "created_by": order.created_by,
#                 "updated_by": order.updated_by,
#                 "address_line1": address.address_line1 if address else None,
#                 "address_line2": address.address_line2 if address else None,
#                 "city": address.city if address else None,
#                 "state": address.state if address else None,
#                 "pincode": address.pincode if address else None,
#                 "user_name": user.name if user else None,
#                 "user_mobile": user.mobile_no if user else None,
#                 "address_details": {
#                     "address_line1": address.address_line1 if address else None,
#                     "address_line2": address.address_line2 if address else None,
#                     "city": address.city if address else None,
#                     "state": address.state if address else None,
#                     "pincode": address.pincode if address else None,
#                 } if address else None,
#                 "items": order_items_dicts,
#                 "order_items": order_items_dicts
#             }
                
#             response_orders.append(OrderResponse(**order_data))
        
#         return response_orders
        
#     except Exception as e:
#         print(f"Error in read_orders: {str(e)}")
#         import traceback
#         print(f"Traceback: {traceback.format_exc()}")
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

# @router.get("/{order_id}", response_model=OrderResponse)
# def read_order(
#     order_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     print(f" Checking order {order_id} for user {current_user.user_id} (Role: {current_user.role})")
    
#     order = db.get(Order, order_id)
    
#     if not order:
#         print(f" Order {order_id} not found")
#         raise HTTPException(status_code=404, detail="Order not found")
    
#     print(f" Order found - User ID: {order.user_id}, Current User ID: {current_user.user_id}")
    
#     # Check permissions
#     if current_user.role.lower() not in ["staff", "admin"] and order.user_id != current_user.user_id:
#         print(f" Permission denied - Order belongs to user {order.user_id}, but current user is {current_user.user_id}")
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     print(f" Access granted to order {order_id}")
#     return order

# @router.put("/{order_id}", response_model=OrderResponse)
# def update_order(
#     order_id: int,
#     order_update: OrderUpdate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     order = db.get(Order, order_id)
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
    
#     # Only staff/admin can update order status
#     if current_user.role not in ["staff", "admin"]:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     # for key, value in order_update.dict(exclude_unset=True).items():
#     #     setattr(order, key, value)
    
#     # Update fields
#     update_data = order_update.dict(exclude_unset=True)
#     for key, value in update_data.items():
#         setattr(order, key, value)
    
#     order.updated_at = datetime.utcnow()
#     order.updated_by = current_user.email

#     db.add(order)
#     db.commit()
#     db.refresh(order)
#     return order

# @router.delete("/{order_id}")
# def delete_order(
#     order_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     order = db.get(Order, order_id)
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
    
#     if current_user.role not in ["staff", "admin"] and order.user_id != current_user.user_id:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     db.delete(order)
#     db.commit()
#     return {"message": "Order deleted successfully"}

@router.get("/", response_model=List[OrderResponse])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    service: Optional[ServiceType] = None,
    status: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        print(f"Fetching orders for user: {current_user.user_id}, Role: {current_user.role}")
        
        # Build query
        if current_user.role in ["staff", "admin"]:
            query = db.query(Order)
        else:
            query = db.query(Order).filter(Order.user_id == current_user.user_id)
        
        # Apply filters with status mapping
        if service:
            query = query.filter(Order.service == service)
        if status:
            # Map frontend status to database status
            status_mapping = {
                "pending": "pending",
                "confirmed": "confirmed",      
                "picked_up": "picked",        
                "completed": "ready",         
                "in_progress": "in_progress", 
                "delivered": "delivered"      
            }
            db_status = status_mapping.get(status.value, status.value)
            query = query.filter(Order.status == db_status)
            
        # Apply pagination and execute
        orders = query.offset(skip).limit(limit).all()
        
        print(f"Found {len(orders)} orders")
        
        # Build response with status mapping
        response_orders = []
        for order in orders:
            try:
                # Map database status to frontend status
                status_mapping = {
                    "pending": "pending",
                    "confirmed": "confirmed",      
                    "picked": "picked_up",        
                    "ready": "completed",         
                    "in_progress": "in_progress", 
                    "delivered": "delivered",
                    "cancelled": "cancelled"
                }
                frontend_status = status_mapping.get(order.status, order.status)
                
                print(f" Mapped status: {order.status} -> {frontend_status}")
                
                # Get order items with error handling
                try:
                    order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
                except Exception as e:
                    print(f"Error fetching items for order {order.order_id}: {e}")
                    order_items = []  # Empty list if error
                
                # Map item statuses with error handling
                order_items_dicts = []
                for item in order_items:
                    try:
                        item_status_mapping = {
                            "pending": "pending",
                            "confirmed": "confirmed",
                            "processed": "processed",  # Add this mapping
                            "picked": "picked_up",
                            "ready": "completed",
                            "in_progress": "in_progress",
                            "delivered": "delivered"
                        }
                        item_frontend_status = item_status_mapping.get(item.status, "pending")  # Default to pending
                        
                        order_items_dicts.append({
                            "order_item_id": item.order_item_id,
                            "order_id": item.order_id,
                            "category_name": item.category_name,
                            "product_name": item.product_name,
                            "quantity": item.quantity,
                            "service": item.service,
                            "status": item_frontend_status,
                            "created_at": item.created_at,
                            "updated_at": item.updated_at,
                            "created_by": item.created_by,
                            "updated_by": item.updated_by
                        })
                    except Exception as e:
                        print(f"Error processing item {getattr(item, 'order_item_id', 'unknown')}: {e}")
                        continue  # Skip this item
                
                # Load address and user
                address = db.query(Address).filter(Address.address_id == order.address_id).first()
                user = db.query(User).filter(User.user_id == order.user_id).first()

                order_data = {
                    "order_id": order.order_id,
                    "user_id": order.user_id,
                    "address_id": order.address_id,
                    "Token_no": order.Token_no,
                    "service": order.service,
                    "status": frontend_status,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "created_by": order.created_by,
                    "updated_by": order.updated_by,
                    "address_line1": address.address_line1 if address else None,
                    "address_line2": address.address_line2 if address else None,
                    "city": address.city if address else None,
                    "state": address.state if address else None,
                    "pincode": address.pincode if address else None,
                    "user_name": user.name if user else None,
                    "user_mobile": user.mobile_no if user else None,
                    "address_details": {
                        "address_line1": address.address_line1 if address else None,
                        "address_line2": address.address_line2 if address else None,
                        "city": address.city if address else None,
                        "state": address.state if address else None,
                        "pincode": address.pincode if address else None,
                    } if address else None,
                    "items": order_items_dicts,
                    "order_items": order_items_dicts
                }
                    
                print(f" Order {order.order_id} data prepared with status: {frontend_status}")
                response_orders.append(OrderResponse(**order_data))
                
            except Exception as order_error:
                print(f"Error processing order {order.order_id}: {order_error}")
                continue  # Skip this order and continue with others
        
        print(f" Successfully processed {len(response_orders)} orders")
        return response_orders
        
    except Exception as e:
        print(f"Error in read_orders: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{order_id}", response_model=OrderResponse)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        print(f"Checking order {order_id} for user {current_user.user_id}")
        
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        
        if current_user.role.lower() not in ["staff", "admin"] and order.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        order_status = order.status
        if order_status == "picked":
            order_status = "picked_up"

        
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
        
        
        order_items_dicts = []
        for item in order_items:
            item_status = item.status
            if item_status == "picked":
                item_status = "picked_up"
            order_items_dicts.append({
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
        
        address = db.query(Address).filter(Address.address_id == order.address_id).first()
        user = db.query(User).filter(User.user_id == order.user_id).first()
        
        
        order_data = {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "address_id": order.address_id,
            "Token_no": order.Token_no,
            "service": order.service,
            "status": order.status,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "created_by": order.created_by,
            "updated_by": order.updated_by,
            "address_line1": address.address_line1 if address else None,
            "address_line2": address.address_line2 if address else None,
            "city": address.city if address else None,
            "state": address.state if address else None,
            "pincode": address.pincode if address else None,
            "user_name": user.name if user else None,
            "user_mobile": user.mobile_no if user else None,
            "address_details": {
                "address_line1": address.address_line1 if address else None,
                "address_line2": address.address_line2 if address else None,
                "city": address.city if address else None,
                "state": address.state if address else None,
                "pincode": address.pincode if address else None,
            } if address else None,
            "items": order_items_dicts,
            "order_items": order_items_dicts
        }
        
        return OrderResponse(**order_data)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in read_order: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        print(f" Updating order {order_id} with data: {order_update.dict(exclude_unset=True)}")
        print(f" Requested by user: {current_user.name} (Role: {current_user.role})")
        
       
        order = db.get(Order, order_id)
        if not order:
            print(f" Order {order_id} not found")
            raise HTTPException(status_code=404, detail="Order not found")
        
        print(f" Found order: {order.Token_no} (Status: {order.status})")
        
        
        if current_user.role not in ["staff", "admin"]:
            print(f" Permission denied for user: {current_user.role}")
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        print(f" Permission granted for {current_user.role}")
        
        
        update_data = order_update.dict(exclude_unset=True)
        print(f" Update data: {update_data}")
        
        old_status = order.status
        new_status = update_data.get('status')
        
        if new_status and new_status != old_status:
            print(f" Status changing: {old_status} → {new_status}")
            
            current_time = datetime.utcnow()
            current_user_email = current_user.email or current_user.name
            
            if new_status == "picked_up":
                order.picked_at = current_time
                order.picked_by = current_user_email
                print(f"  Set picked_at: {current_time}, picked_by: {current_user_email}")
                
            elif new_status == "delivered":
                order.delivered_at = current_time
                order.delivered_by = current_user_email
                print(f"  Set delivered_at: {current_time}, delivered_by: {current_user_email}")
                
            elif new_status == "cancelled":
                order.cancelled_at = current_time
                order.cancelled_by = current_user_email
                print(f"  Set cancelled_at: {current_time}, cancelled_by: {current_user_email}")
            
            
            order.status = new_status

        items_data = update_data.pop('items', None)
        if items_data is not None:
            print(f" Processing {len(items_data)} order items")
            update_order_items(db, order.order_id, items_data, current_user.name)  
        
        
        order_fields_updated = False
        for field in ['status', 'service', 'Token_no', 'delivery_agent_id', 'priority', 'special_instructions']:
            if field in update_data and update_data[field] is not None:
                old_value = getattr(order, field, None)
                new_value = update_data[field]
                setattr(order, field, new_value)
                order_fields_updated = True
                print(f"Updated {field}: {old_value} → {new_value}")
        
        
        address_updated = False
        address_fields = ['address_line1', 'address_line2', 'city', 'state', 'pincode']
        if any(field in update_data for field in address_fields):
            address = db.get(Address, order.address_id)
            if address:
                for field in address_fields:
                    if field in update_data and update_data[field] is not None:
                        old_value = getattr(address, field, None)
                        new_value = update_data[field]
                        setattr(address, field, new_value)
                        address_updated = True
                        print(f" Updated address {field}: {old_value} → {new_value}")
        
        
        user_updated = False
        if 'name' in update_data and update_data['name'] is not None:
            user = db.get(User, order.user_id)
            if user and current_user.role in ["staff", "admin"]:
                old_value = user.name
                new_value = update_data['name']
                user.name = new_value
                user_updated = True
                print(f" Updated user name: {old_value} → {new_value}")
        
        if 'mobile' in update_data and update_data['mobile'] is not None:
            user = db.get(User, order.user_id)
            if user and current_user.role in ["staff", "admin"]:
                old_value = user.mobile_no
                new_value = update_data['mobile']
                user.mobile_no = new_value
                user_updated = True
                print(f" Updated user mobile: {old_value} → {new_value}")
        
        
        order.updated_at = datetime.utcnow()
        order.updated_by = current_user.name or current_user.email
        
        
        db.add(order)
        if address_updated:
            db.add(address)
        if user_updated:
            db.add(user)
        
        db.commit()
        db.refresh(order)
        
        print(f"Order {order_id} updated successfully")
        
        
        return read_order(order_id, db, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating order {order_id}: {str(e)}")
        import traceback
        print(f" Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update order: {str(e)}"
        )


def update_order_items(db: Session, order_id: int, items_data: List[dict], updated_by: str):
    """Update order items - handles both existing and new items"""
    try:
        print(f" Starting order items update for order {order_id}")
        
        
        existing_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        existing_items_dict = {item.order_item_id: item for item in existing_items}
        
        print(f" Existing items: {[item.order_item_id for item in existing_items]}")
        print(f" New items data: {items_data}")
        
        updated_items = []
        new_items = []
        
        for item_data in items_data:
            item_id = item_data.get('order_item_id')
            
            if item_id and item_id in existing_items_dict:
                
                existing_item = existing_items_dict[item_id]
                print(f" Updating existing item {item_id}")
                
                
                for field in ['category_name', 'product_name', 'quantity', 'service', 'status']:
                    if field in item_data and item_data[field] is not None:
                        old_value = getattr(existing_item, field)
                        new_value = item_data[field]
                        setattr(existing_item, field, new_value)
                        print(f"   {field}: {old_value} → {new_value}")
                
                existing_item.updated_at = datetime.utcnow()
                existing_item.updated_by = updated_by
                db.add(existing_item)
                updated_items.append(existing_item)
                
                
                del existing_items_dict[item_id]
                
            else:
                
                print(f" Creating new item for order {order_id}")
                new_item = OrderItem(
                    order_id=order_id,
                    category_name=item_data['category_name'],
                    product_name=item_data['product_name'],
                    quantity=item_data['quantity'],
                    service=item_data.get('service', 'wash_iron'),
                    status=item_data.get('status', 'pending'),
                    created_by=updated_by,
                    updated_by=updated_by,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_item)
                new_items.append(new_item)
        
        
        deleted_items = []
        for item_id, item in existing_items_dict.items():
            print(f" Deleting item {item_id} that was removed from order")
            db.delete(item)
            deleted_items.append(item_id)
        
        
        db.commit()
        
        
        for item in new_items:
            db.refresh(item)
        
        print(f"    Items update completed:")
        print(f"    Updated: {len(updated_items)} items")
        print(f"    Created: {len(new_items)} items") 
        print(f"    Deleted: {len(deleted_items)} items")
        
    except Exception as e:
        db.rollback()
        print(f" Error updating order items: {str(e)}")
        raise
    
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


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Quick endpoint to update only order status"""
    try:
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if current_user.role not in ["staff", "admin"]:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        new_status = status_update.get('status')
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        order.status = new_status
        order.updated_at = datetime.utcnow()
        order.updated_by = current_user.email
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        return {"message": "Order status updated successfully", "status": order.status}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update order status: {str(e)}")
    
@router.get("/user/{user_id}", response_model=UserOrdersResponse)
def get_orders_by_user(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    service: Optional[ServiceType] = None,
    status: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all orders for a specific user with total count"""
    try:
        print(f"Fetching orders for user ID: {user_id} by user: {current_user.user_id}")
        
        
        if current_user.role not in ["staff", "admin"] and current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view other users' orders"
            )
        
        
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        
        query = db.query(Order).filter(Order.user_id == user_id)
        
        
        if service:
            query = query.filter(Order.service == service)
        if status:
            query = query.filter(Order.status == status)
        
        
        total_orders = query.count()
        print(f"Total orders for user {user_id}: {total_orders}")
        
       
        orders = query.offset(skip).limit(limit).all()
        
        print(f"Found {len(orders)} orders for user {user_id} (showing {skip} to {skip + len(orders)})")
        
        
        response_orders = []
        for order in orders:
            
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
            
            
            order_items_dicts = []
            for item in order_items:
                order_items_dicts.append({
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
            
           
            address = db.query(Address).filter(Address.address_id == order.address_id).first()
            
            
            order_data = {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "address_id": order.address_id,
                "Token_no": order.Token_no,
                "service": order.service,
                "status": order.status,
                "created_at": order.created_at,
                "updated_at": order.updated_at,
                "created_by": order.created_by,
                "updated_by": order.updated_by,
                "address_line1": address.address_line1 if address else None,
                "address_line2": address.address_line2 if address else None,
                "city": address.city if address else None,
                "state": address.state if address else None,
                "pincode": address.pincode if address else None,
                "user_name": user.name if user else None,
                "user_mobile": user.mobile_no if user else None,
                "address_details": {
                    "address_line1": address.address_line1 if address else None,
                    "address_line2": address.address_line2 if address else None,
                    "city": address.city if address else None,
                    "state": address.state if address else None,
                    "pincode": address.pincode if address else None,
                } if address else None,
                "items": order_items_dicts,
                "order_items": order_items_dicts
            }
            
            response_orders.append(OrderResponse(**order_data))
        
        
        user_details = {
            "user_id": user.user_id,
            "name": user.name,
            "mobile_no": user.mobile_no,
            "email": user.email,
            "role": user.role
        }
        
        
        return UserOrdersResponse(
            orders=response_orders,
            total_orders=total_orders,
            user_details=user_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching user orders: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user orders: {str(e)}"
        )



    # ------------------------------------------------------------
    
from dependencies.auth import get_current_user_optional  
@router.post("/public/", response_model=OrderResponse)
def create_public_order(
    order: OrderCreate,
    db: Session = Depends(get_db)
):
    try:
        print(f" Creating PUBLIC order for: {order.customer_name} ({order.customer_mobile})")
        print(f" Request data: {order.dict()}")

       
        if not order.customer_name or not order.customer_mobile:
            raise HTTPException(status_code=400, detail="Customer name and mobile are required")

        
        for index, item in enumerate(order.items):
            if not item.category_name or item.category_name.strip() == "":
                raise HTTPException(status_code=400, detail=f"Item {index+1}: Category name is required")
            if not item.product_name or item.product_name.strip() == "":
                raise HTTPException(status_code=400, detail=f"Item {index+1}: Product name is required")

        
        guest_user = get_or_create_guest_user(db, order.customer_name, order.customer_mobile)
        print(f" Guest user: {guest_user.name} (ID: {guest_user.user_id})")

        # guest_identifier = f"Guest: {order.customer_mobile}"

        new_address = Address(
            user_id=guest_user.user_id,
            name=order.customer_name,        
            mobile_no=order.customer_mobile, 
            address_line1=order.address_line1.strip(),
            address_line2=order.address_line2.strip() if order.address_line2 else "",
            city=order.city.strip(),
            state=order.state.strip(),
            pincode=order.pincode.strip(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_address)
        db.commit()
        db.refresh(new_address)
        print(f" Address created: {new_address.address_id}")

        initial_status = "pending"
        print(f" Public/Guest order - Status: {initial_status}")
        
        db_order = Order(
            user_id=guest_user.user_id,
            address_id=new_address.address_id,
            Token_no=generate_Token_no(),
            service=order.service,
            status=initial_status,
            created_by=f"Guest: {order.customer_name}",  
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        print(f" Order created: {db_order.Token_no}")

        
        created_items = []
        for item in order.items:
            db_item = OrderItem(
                order_id=db_order.order_id,
                category_name=item.category_name,
                product_name=item.product_name,
                quantity=item.quantity,
                service=order.service,
                unit_price=getattr(item, 'unit_price', 10.0),
                status="pending",
                created_by=f"Guest: {order.customer_name}",  
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(db_item)
            created_items.append(db_item)
        
        db.commit()

        
        for item in created_items:
            db.refresh(item)

        
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

        
        response_data = {
            "order_id": db_order.order_id,
            "user_id": db_order.user_id,
            "address_id": db_order.address_id,
            "Token_no": db_order.Token_no,
            "service": db_order.service,
            "status": db_order.status,
            "created_at": db_order.created_at,
            "updated_at": db_order.updated_at,
            "created_by": f"Guest: {order.customer_name}",
            "updated_by": None,
            "order_items": items_response,
            "items": items_response,
            "user_name": order.customer_name,
            "user_mobile": order.customer_mobile,
            "address_line1": order.address_line1,
            "address_line2": order.address_line2,
            "city": order.city,
            "state": order.state,
            "pincode": order.pincode,
            "address_details": {
                "address_line1": order.address_line1,
                "address_line2": order.address_line2,
                "city": order.city,
                "state": order.state,
                "pincode": order.pincode,
            }
        }

        print(f" Order {db_order.Token_no} created for {order.customer_name}")
        return OrderResponse(**response_data)

    except Exception as e:
        db.rollback()
        print(f" Order creation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")