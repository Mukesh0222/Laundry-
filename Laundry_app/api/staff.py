from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
import random
import string
from datetime import datetime, date
from sqlalchemy import func  

from db.session import get_db
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate, StaffOrderCreate
from dependencies.auth import get_current_user, get_current_staff_user
from models.user import User
from sqlalchemy.orm import selectinload
from models.address import Address

router = APIRouter()


def get_user_identifier(user: User) -> str:
    """Get user identifier (mobile_no) for created_by/updated_by fields"""
    return user.mobile_no or user.name or "Unknown"

def convert_category_name(category):
    """Convert enum category names to display names"""
    if not category:
        return "Others"
    
    mapping = {
        'MENS_CLOTHING': "Men's Clothing",
        'WOMENS_CLOTHING': "Women's Clothing", 
        'KIDS_CLOTHING': "Kids Clothing",
        'HOUSE_HOLDS': "House Holds",
        'OTHERS': "Others",
        "Men's Clothing": "Men's Clothing",  
        "Women's Clothing": "Women's Clothing",
        "Kids Clothing": "Kids Clothing",
        "House Holds": "House Holds",
        "Others": "Others"
    }
    return mapping.get(category, "Others")


def convert_product_name(product):
    """Convert enum product names to display names"""
    if not product:
        return "Other"
    
    mapping = {
        
        'T_SHIRT': "T-Shirt",
        'SHIRT': "Shirt", 
        'JEANS': "Jeans",
        'TROUSERS': "Trousers",
        'SHORTS': "Shorts",
        'INNERWEAR': "Innerwear",
        'FORMAL_SHIRT': "Formal Shirt",
        'CASUAL_SHIRT': "Casual Shirt",
        'JACKET': "Jacket",
        'SWEATER': "Sweater",
        
        
        'SAREE': "Saree",
        'KURTI': "Kurti",
        'DRESS': "Dress",
        'BLOUSE': "Blouse", 
        'SKIRT': "Skirt",
        'TOP': "Top",
        'LEHENGA': "Lehenga",
        'SALWAR': "Salwar",
        'DUPATTA': "Dupatta",
        'NIGHT_DRESS': "Night Dress",
        
        
        'KIDS_TSHIRT': "Kids T-shirt",
        'KIDS_SHORTS': "Kids Shorts",
        'SCHOOL_UNIFORM': "School Uniform",
        'FROCK': "Frock",
        'PYJAMAS': "Pyjamas",
        'KIDS_JEANS': "Kids Jeans",
        'BABY_SUIT': "Baby Suit",
        'ROMPER': "Romper",
        'KIDS_JACKET': "Kids Jacket",
        'KIDS_SWEATER': "Kids Sweater",
        
        
        'BEDSHEET': "Bedsheet",
        'PILLOW_COVER': "Pillow Cover",
        'CURTAIN': "Curtain",
        'TABLE_CLOTH': "Table Cloth",
        'TOWEL': "Towel",
        'BLANKET': "Blanket",
        'CARPET': "Carpet",
        'BED_COVER': "Bed Cover",
        'CUSHION_COVER': "Cushion Cover",
        'MATTRESS_COVER': "Mattress Cover",
        
        
        'BAG': "Bag",
        'CAP': "Cap",
        'SCARF': "Scarf",
        'GLOVES': "Gloves",
        'SOCKS': "Socks",
        'HANDKERCHIEF': "Handkerchief",
        'BELT': "Belt",
        'TIE': "Tie",
        'STOLE': "Stole",
        'MUFFLER': "Muffler"
    }
    if product in mapping.values():
        return product
    return mapping.get(product, "Other")

def convert_order_status(status):
    """Convert order status to valid enum values - SAFE VERSION"""
    if not status:
        return OrderStatus.PENDING
    
    status_lower = str(status).lower().strip()
    print(f"DEBUG: Converting status '{status}' to lowercase '{status_lower}'")
    
    if status_lower in ['pending', 'PENDING']:
        return OrderStatus.PENDING
    elif status_lower in ['confirmed', 'CONFIRMED']:
        return OrderStatus.CONFIRMED
    elif status_lower in ['processed', 'PROCESSED', 'in_progress', 'IN_PROGRESS']:
        return OrderStatus.PROCESSED  
    elif status_lower in ['picked_up', 'PICKED_UP', 'picked', 'PICKED']:
        return OrderStatus.PICKED_UP
    elif status_lower in ['completed', 'COMPLETED', 'delivered', 'DELIVERED']:
        return OrderStatus.COMPLETED  
    elif status_lower in ['cancelled', 'CANCELLED']:
        return OrderStatus.CANCELLED
    else:
        print(f"DEBUG: Unknown status '{status_lower}', defaulting to PENDING")
        return OrderStatus.PENDING
    
def convert_service_type(service):
    """Convert service type to valid enum values"""
    if not service:
        return "wash_iron"
    
    service_mapping = {
        'wash_iron': "wash_iron",
        'WASH_IRON': "wash_iron",
        'dry_cleaning': "dry_cleaning", 
        'DRY_CLEANING': "dry_cleaning",
        'wash_only': "wash_only",
        'WASH_ONLY': "wash_only",
        'iron_only': "iron_only",
        'IRON_ONLY': "iron_only",
        'pending': "wash_iron",  
        'PENDING': "wash_iron",
    }
    return service_mapping.get(service, "wash_iron")

def generate_order_number():
    """Generate unique order number"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD{date_str}-{random_str}"

def generate_token(db: Session) -> str:
    """Generate unique Token_no with retry logic"""
    max_retries = 5
    for attempt in range(max_retries):
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        token_no = f"ORD{date_str}-{random_str}"
        
        existing_order = db.query(Order).filter(Order.Token_no == token_no).first()
        if not existing_order:
            return token_no
        
        print(f" Token_no {token_no} already exists, retrying... (attempt {attempt + 1})")
    

    fallback_token = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    print(f" Using fallback token: {fallback_token}")
    return fallback_token

def get_created_by_identifier(current_user: User, order_data) -> str:
    """Get created_by identifier - always use customer details"""
    print(f" DEBUG get_created_by_identifier:")
    print(f"   - Current User: {current_user.name} (Role: {current_user.role})")
    
    if hasattr(order_data, 'customer_name') and hasattr(order_data, 'customer_mobile'):
        customer_name = getattr(order_data, 'customer_name', None)
        customer_mobile = getattr(order_data, 'customer_mobile', None)
        
        print(f"   - Order Customer Name: '{customer_name}'")
        print(f"   - Order Customer Mobile: '{customer_mobile}'")
        
        if customer_name and customer_mobile:
            result = f"Customer: {customer_name} ({customer_mobile})"
            print(f" Using customer details: {result}")
            return result
    
    customer_id = 99  # Your target customer ID
    customer = current_user._sa_instance_state.session.get(User, customer_id)
    if customer:
        result = f"Customer: {customer.name} ({customer.mobile_no})"
        print(f"Using target customer details: {result}")
        return result
    
    result = f"Customer: {current_user.name} ({current_user.mobile_no})"
    print(f" Fallback to current user: {result}")
    return result

@router.post("/", response_model=OrderResponse)
def create_order(
    order_data: StaffOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Create a new order (Staff can create orders for any customer)"""
    try:
        print(f" NEW FILE - Staff creating order. Staff ID: {current_user.user_id}")
        
        created_by_identifier = get_created_by_identifier(current_user, order_data)
        print(f" Final created_by identifier: {created_by_identifier}")

        token_no = generate_token(db)
        
        customer = db.get(User, 99)        
        if not customer:
            
            customer = current_user
        
        print(f" Using customer: {customer.name} (ID: {customer.user_id})")
        
        
        from models.address import Address
        customer_address = Address(
            user_id=customer.user_id,
            name=customer.name,
            mobile_no=customer.mobile_no,
            address_line1=order_data.address_line1,
            address_line2=order_data.address_line2,
            city=order_data.city,
            state=order_data.state,
            pincode=order_data.pincode,
            # landmark=order_data.landmark
        )
        db.add(customer_address)
        db.commit()
        db.refresh(customer_address)
        print(f" Created address: {customer_address.address_id}")
        
        
        db_order = Order(
            user_id=customer.user_id,
            address_id=customer_address.address_id,
            Token_no=token_no,
            service=order_data.service,
            status=OrderStatus.PENDING,
            created_by=created_by_identifier,
            updated_by=created_by_identifier
        )
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        print(f"Order created: {db_order.Token_no}")
        print(f"Order user_id: {db_order.user_id} (Customer)")
        print(f"Order created_by: {db_order.created_by} (Customer details)")
        
        merged_items = {}
        if order_data.items:
            for item_data in order_data.items:
                key = f"{item_data.category_name}_{item_data.product_name}"
                if key in merged_items:
                    
                    merged_items[key].quantity += item_data.quantity
                else:
                    
                    merged_items[key] = item_data
        
        print(f" Original items: {len(order_data.items)}, Merged items: {len(merged_items)}")

        
        created_items = []
        for key, item_data in merged_items.items():
            db_item = OrderItem(
                order_id=db_order.order_id,
                category_name=item_data.category_name,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                service=order_data.service,
                status="pending",  
                created_at=datetime.utcnow(),  
                updated_at=datetime.utcnow(),  
                created_by=created_by_identifier,  
                updated_by=created_by_identifier 
            )
            db.add(db_item)
            created_items.append(db_item)
            
            db.commit()
            
            for item in created_items:
                db.refresh(item)
        
        
        user = db.get(User, db_order.user_id)
        address = db.get(Address, db_order.address_id)
        
        
        order_items = db.exec(
            select(OrderItem).where(OrderItem.order_id == db_order.order_id)
        ).all()
        
        
        items_response = []
        for item in order_items:
            items_response.append({
                "order_item_id": item.order_item_id,
                "order_id": item.order_id,
                "category_name": convert_category_name(item.category_name),
                "product_name": convert_product_name(item.product_name),
                "quantity": item.quantity,
                "service": convert_service_type(item.service),
                "status": convert_order_status(item.status).value,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "created_by": item.created_by,
                "updated_by": item.updated_by
            })
        
        
        address_details = None
        if address:
            address_details = {
                "address_line1": address.address_line1,
                "address_line2": address.address_line2,
                "city": address.city,
                "state": address.state,
                "pincode": address.pincode,
                # "landmark": address.landmark
            }
        
        
        response_data = {
            "order_id": db_order.order_id,
            "user_id": db_order.user_id,
            "address_id": db_order.address_id,
            "Token_no": db_order.Token_no,
            "service": convert_service_type(db_order.service),
            "status": convert_order_status(db_order.status).value,
            "created_at": db_order.created_at,
            "updated_at": db_order.updated_at,
            "created_by": db_order.created_by,
            "updated_by": db_order.updated_by,
            
            "address_line1": order_data.address_line1,
            "address_line2": order_data.address_line2,
            "city": order_data.city,
            "state": order_data.state,
            "pincode": order_data.pincode,
            # "landmark": order_data.landmark,
            
            "user_name": user.name if user else None,
            "user_mobile": user.mobile_no if user else None,
            
            "address_details": address_details,
            "items": items_response,
            "order_items": items_response
        }
        
        return OrderResponse(**response_data)
        
    except Exception as e:
        db.rollback()
        print(f" Staff order creation error: {str(e)}")
        import traceback
        print(f" Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Staff order creation failed: {str(e)}")


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get specific order by ID"""
    try:
        print(f"Getting order: {order_id}")
        
        
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        print(f"Order found - ID: {order.order_id}, service: {order.service}, status: {order.status}")
        
        
        user = db.get(User, order.user_id)
        address = db.get(Address, order.address_id)
        
        
        order_items = db.exec(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).all()
        
        
        items_response = []
        for item in order_items:
            items_response.append({
                "order_item_id": item.order_item_id,
                "order_id": item.order_id,
                "category_name": convert_category_name(item.category_name),
                "product_name": convert_product_name(item.product_name),
                "quantity": item.quantity,
                "service": convert_service_type(item.service),
                "status": convert_order_status(item.status).value,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
                "created_by": item.created_by,
                "updated_by": item.updated_by
            })
        
        
        address_details = None
        if address:
            address_details = {
                "address_line1": address.address_line1,
                "address_line2": address.address_line2,
                "city": address.city,
                "state": address.state,
                "pincode": address.pincode,
                # "landmark": address.landmark
            }
        
        order_status = convert_order_status(order.status)
        order_service = convert_service_type(order.service)

        
        response_data = {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "address_id": order.address_id,
            "Token_no": order.Token_no,
            "service": order_service,
            "status": order_status.value,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "created_by": order.created_by,
            "updated_by": order.updated_by,
            
            "address_line1": address.address_line1 if address else "",
            "address_line2": address.address_line2 if address else "",
            "city": address.city if address else "",
            "state": address.state if address else "",
            "pincode": address.pincode if address else "",
            # "landmark": address.landmark if address else "",
            
            "user_name": user.name if user else None,
            "user_mobile": user.mobile_no if user else None,
            
            "address_details": address_details,
            "items": items_response,
            "order_items": items_response
        }
        
        return OrderResponse(**response_data)
        
    except Exception as e:
        print(f"Get order error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get order: {str(e)}")


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get all orders with search and status filters"""
    try:
        print(f"Staff getting orders. Staff ID: {current_user.user_id}")
        
        statement = select(Order)
        
        
        if status:
            valid_status = convert_order_status(status)
            statement = statement.where(Order.status == valid_status.value)
        
        
        if search:
            search = f"%{search}%"
            statement = statement.where(Order.Token_no.ilike(search))
        
        statement = statement.offset(skip).limit(limit).order_by(Order.created_at.desc())
        orders = db.exec(statement).all()
        
        print(f"Found {len(orders)} orders")
        
        orders_response = []
        for order in orders:
            try:
                print(f"Processing order {order.order_id}")
                print(f"  Raw service: '{order.service}' (type: {type(order.service).__name__})")
                print(f"  Raw status: '{order.status}' (type: {type(order.status).__name__})")
                
                
                user = db.get(User, order.user_id)
                address = db.get(Address, order.address_id)
                
                
                order_items = db.exec(
                    select(OrderItem).where(OrderItem.order_id == order.order_id)
                ).all()
                
                
                items_response = []
                for item in order_items:
                    items_response.append({
                        "order_item_id": item.order_item_id,
                        "order_id": item.order_id,
                        "category_name": convert_category_name(item.category_name),
                        "product_name": convert_product_name(item.product_name),
                        "quantity": item.quantity,
                        "service": convert_service_type(item.service),
                        "status": convert_order_status(item.status).value,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                        "created_by": item.created_by,
                        "updated_by": item.updated_by
                    })
                
                
                address_details = None
                if address:
                    address_details = {
                        "address_line1": address.address_line1,
                        "address_line2": address.address_line2,
                        "city": address.city,
                        "state": address.state,
                        "pincode": address.pincode
                    }
                
                
                order_service = convert_service_type(order.service)
                order_status = convert_order_status(order.status)
                
                print(f"  Converted service: '{order_service}'")
                print(f"  Converted status: '{order_status.value}'")
                
                
                response_dict = {
                    "order_id": order.order_id,
                    "user_id": order.user_id,
                    "address_id": order.address_id,
                    "Token_no": order.Token_no,
                    "service": order_service,  
                    "status": order_status.value,  
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "created_by": order.created_by,
                    "updated_by": order.updated_by,
                    "address_line1": address.address_line1 if address else "",
                    "address_line2": address.address_line2 if address else "",
                    "city": address.city if address else "",
                    "state": address.state if address else "",
                    "pincode": address.pincode if address else "",
                    "user_name": user.name if user else None,
                    "user_mobile": user.mobile_no if user else None,
                    "address_details": address_details,
                    "items": items_response,
                    "order_items": items_response
                }
                
                
                print(f"  Final service for response: '{response_dict['service']}'")
                print(f"  Final status for response: '{response_dict['status']}'")
                
                
                order_response = OrderResponse(**response_dict)
                orders_response.append(order_response)
                print(f"   Successfully processed order {order.order_id}")
                
            except Exception as order_error:
                print(f"   Error processing order {order.order_id}: {str(order_error)}")
                import traceback
                print(f"  Order error details: {traceback.format_exc()}")
                continue
        
        print(f"Successfully processed {len(orders_response)} orders")
        return orders_response
        
    except Exception as e:
        print(f"Get orders error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")



@router.get("/user/{user_id}/orders", response_model=List[OrderResponse])
def get_orders_by_user(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    service: Optional[str] = Query(None, description="Filter by service type"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get all orders for a specific user (Staff only)"""
    try:
        print(f"Staff getting orders for user: {user_id}")
        
        customer = db.get(User, user_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        print(f"Customer found: {customer.name} (ID: {customer.user_id}, Mobile: {customer.mobile_no})")
        
        query = db.query(Order).filter(Order.user_id == user_id)

        if service:
            valid_service = convert_service_type(service)
            query = query.filter(Order.service == valid_service)
            print(f"Filtering by service: {valid_service}")
            
        if status:
            valid_status = convert_order_status(status)
            query = query.filter(Order.status == valid_status.value)
            print(f"Filtering by status: {valid_status.value}")

        total_count = query.count()
        print(f"Total orders found for customer {customer.name}: {total_count}")

        query = query.order_by(Order.created_at.desc())
        orders = query.offset(skip).limit(limit).all() 

        print(f"Returning {len(orders)} orders for user {user_id} (showing {skip} to {skip + len(orders)})")
        
        orders_response = []
        for order in orders:
            try:
                print(f"Processing order {order.order_id} - Status: {order.status}")
                
                order_customer = db.get(User, order.user_id)
                
               
                address = db.get(Address, order.address_id)
                
              
                order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
                
                print(f"Found {len(order_items)} items for order {order.Token_no}")
                
               
                items_response = []
                for item in order_items:
                    items_response.append({
                        "order_item_id": item.order_item_id,
                        "order_id": item.order_id,
                        "category_name": convert_category_name(item.category_name),
                        "product_name": convert_product_name(item.product_name),
                        "quantity": item.quantity,
                        "service": convert_service_type(item.service),
                        "status": convert_order_status(item.status).value,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                        "created_by": item.created_by,
                        "updated_by": item.updated_by
                    })
                
                
                address_details = None
                if address:
                    address_details = {
                        "address_line1": address.address_line1,
                        "address_line2": address.address_line2,
                        "city": address.city,
                        "state": address.state,
                        "pincode": address.pincode
                    }
                
                
                order_service = convert_service_type(order.service)
                order_status = convert_order_status(order.status)

               
                response_dict = {
                    "order_id": order.order_id,
                    "user_id": order.user_id,
                    "address_id": order.address_id,
                    "Token_no": order.Token_no,
                    "service": order_service,
                    "status": order_status.value,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "created_by": order.created_by,
                    "updated_by": order.updated_by,
                    "address_line1": address.address_line1 if address else "",
                    "address_line2": address.address_line2 if address else "",
                    "city": address.city if address else "",
                    "state": address.state if address else "",
                    "pincode": address.pincode if address else "",
                    "user_name": order_customer.name if order_customer else None,
                    "user_mobile": order_customer.mobile_no if order_customer else None,
                    "address_details": address_details,
                    "items": items_response,
                    "order_items": items_response
                }
                
                
                order_response = OrderResponse(**response_dict)
                orders_response.append(order_response)
                print(f"Successfully processed order {order.order_id}")
                
            except Exception as order_error:
                print(f"Error processing order {order.order_id}: {str(order_error)}")
                import traceback
                print(f"Order error details: {traceback.format_exc()}")
                continue
        
        print(f"Successfully processed {len(orders_response)} orders out of {len(orders)}")
        
        if len(orders_response) == 0:
            print(f" No orders found for customer {customer.name}")
            return []
        
        return orders_response
    except HTTPException:
        raise
      
    except Exception as e:
        print(f"Get user orders error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get user orders: {str(e)}")
    

#  GET /api/v1/staff/orders - Get all orders with filters
# @router.get("/", response_model=List[OrderResponse])
# def get_orders(
#     skip: int = 0,
#     limit: int = 100,
#     status: Optional[OrderStatus] = Query(None),
#     search: Optional[str] = Query(None),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """Get all orders with search and status filters"""
#     try:
#         print(f" Staff getting orders. Staff ID: {current_user.user_id}")
        
#         statement = select(Order).options(
#             selectinload(Order.user),
#             selectinload(Order.address),
#             selectinload(Order.order_items)
#         )
        
#         # Status filter
#         if status:
#             statement = statement.where(Order.status == status)
        
#         # Search filter (by token, user name, mobile)
#         if search:
#             search = f"%{search}%"
#             statement = statement.where(
#                 (Order.Token_no.ilike(search)) |
#                 (Order.user.has(User.name.ilike(search))) |
#                 (Order.user.has(User.mobile_no.ilike(search)))
#             )
        
#         statement = statement.offset(skip).limit(limit).order_by(Order.created_at.desc())
#         orders = db.exec(statement).all()
        
#         return orders
        
#     except Exception as e:
#         print(f" Get orders error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")

# #  POST /api/v1/staff/orders - Create a new order
# # @router.post("/", response_model=OrderResponse)
# # def create_order(
# #     order_data: StaffOrderCreate,
# #     db: Session = Depends(get_db),
# #     current_user: User = Depends(get_current_staff_user)
# # ):
# #     """Create a new order (Staff can create orders for any customer)"""
# #     try:
# #         print(f" Staff creating order. Staff ID: {current_user.user_id}")
        
# #         # Generate order number and token
# #         token_no = generate_token()
        
# #         # Use user ID 99 (python user)
# #         customer = db.get(User, 99)
# #         if not customer:
# #             customer = current_user
        
# #         print(f" Using customer: {customer.name} (ID: {customer.user_id})")
        
# #         # Create address for the customer
# #         from models.address import Address
# #         customer_address = Address(
# #             user_id=customer.user_id,
# #             name=customer.name,
# #             mobile_no=customer.mobile_no,
# #             address_line1="Store Pickup",
# #             city="Chennai",
# #             state="Tamil Nadu",
# #             postal_code="600001"
# #         )
# #         db.add(customer_address)
# #         db.commit()
# #         db.refresh(customer_address)
# #         print(f" Created address: {customer_address.address_id}")
        
# #         # Create order
# #         db_order = Order(
# #             user_id=customer.user_id,
# #             address_id=customer_address.address_id,
# #             Token_no=token_no,
# #             service=order_data.service,
# #             status=OrderStatus.PENDING,
# #             created_by=current_user.email,
# #             updated_by=current_user.email
# #         )
        
# #         db.add(db_order)
# #         db.commit()
# #         db.refresh(db_order)
        
# #         print(f" Order created: {db_order.Token_no}")
        
# #         # Create order items
# #         if order_data.items:
# #             for item_data in order_data.items:
# #                 db_item = OrderItem(
# #                     order_id=db_order.order_id,
# #                     category_name=item_data.category_name,
# #                     product_name=item_data.product_name,
# #                     quantity=item_data.quantity,
# #                     service=order_data.service
# #                 )
# #                 db.add(db_item)
            
# #             db.commit()
# #             db.refresh(db_order)
        
# #         return db_order
        
# #     except Exception as e:
# #         db.rollback()
# #         print(f" Staff order creation error: {str(e)}")
# #         raise HTTPException(status_code=500, detail=f"Staff order creation failed: {str(e)}")

# #  GET /api/v1/staff/orders/{order_id} - Get single order
# @router.get("/{order_id}", response_model=OrderResponse)
# def get_order(
#     order_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """Get specific order by ID"""
#     try:
#         print(f" Getting order: {order_id}")
        
#         order = db.exec(
#             select(Order)
#             .where(Order.order_id == order_id)
#             .options(
#                 selectinload(Order.user),
#                 selectinload(Order.address),
#                 selectinload(Order.order_items)
#             )
#         ).first()
#         if not order:
#             raise HTTPException(status_code=404, detail="Order not found")
        
#         return order
        
#     except Exception as e:
#         print(f" Get order error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to get order: {str(e)}")


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update order status and details"""
    try:
        print(f" Updating order: {order_id}")
        
        user_identifier = get_user_identifier(current_user)
        print(f" User identifier for updated_by: {user_identifier}")

        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        
        update_data = order_update.dict(exclude_unset=True)

        
        if 'status' in update_data and update_data['status']:
            update_data['status'] = convert_order_status(update_data['status']).value
        
         
        if 'service' in update_data and update_data['service']:
            update_data['service'] = convert_service_type(update_data['service'])
        for key, value in update_data.items():
            setattr(order, key, value)
        
        order.updated_at = datetime.utcnow()
        order.updated_by = current_user.email
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        print(f" Order updated: {order.Token_no}")

        
        user = db.get(User, order.user_id)
        address = db.get(Address, order.address_id)
        order_items = db.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
        
        items_response = []
        for item in order_items:
            items_response.append({
                "order_item_id": item.order_item_id,
                "order_id": item.order_id,
                "category_name": convert_category_name(item.category_name),
                "product_name": convert_product_name(item.product_name),
                "quantity": item.quantity,
                "service": convert_service_type(item.service),
                "status": convert_order_status(item.status).value,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            })
        
        address_details = None
        if address:
            address_details = {
                "address_line1": address.address_line1,
                "address_line2": address.address_line2,
                "city": address.city,
                "state": address.state,
                "pincode": address.pincode,
            }
        
        response_data = {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "address_id": order.address_id,
            "Token_no": order.Token_no,
            "service": convert_service_type(order.service),
            "status": convert_order_status(order.status).value,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "created_by": order.created_by,
            "updated_by": order.updated_by,
            "address_line1": address.address_line1 if address else "",
            "address_line2": address.address_line2 if address else "",
            "city": address.city if address else "",
            "state": address.state if address else "",
            "pincode": address.pincode if address else "",
            "user_name": user.name if user else None,
            "user_mobile": user.mobile_no if user else None,
            "address_details": address_details,
            "items": items_response,
            "order_items": items_response
        }
        
        return OrderResponse(**response_data)
        
    except Exception as e:
        db.rollback()
        print(f"Update order error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update order: {str(e)}")



@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Delete order and its items"""
    try:
        print(f" Deleting order: {order_id}")
        
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        
        items_statement = select(OrderItem).where(OrderItem.order_id == order_id)
        order_items = db.exec(items_statement).all()
        for item in order_items:
            db.delete(item)
        
        
        db.delete(order)
        db.commit()
        
        print(f" Order deleted: {order_id}")
        return {"message": "Order deleted successfully"}
        
    except Exception as e:
        db.rollback()
        print(f" Delete order error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete order: {str(e)}")



@router.post("/{order_id}/confirm")
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Quick confirm order"""
    try:
        user_identifier = get_user_identifier(current_user)

        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = OrderStatus.CONFIRMED
        order.updated_at = datetime.utcnow()
        order.updated_by = user_identifier 
        
        db.add(order)
        db.commit()
        
        return {"message": "Order confirmed successfully", "Token_no": order.Token_no}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to confirm order: {str(e)}")

@router.post("/{order_id}/pick")
def pick_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Quick pick order with auto token generation"""
    try:
        print(f" Picking order: {order_id}")

        user_identifier = get_user_identifier(current_user)
        print(f" User identifier for updated_by: {user_identifier}")
        
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        print(f" Order found - ID: {order.order_id}, Token: {order.Token_no}, Status: {order.status}")
        
        
        order.status = OrderStatus.PICKED_UP
        
        
        if not order.Token_no:
            new_token = generate_token()
            order.Token_no = new_token
            print(f" Generated new token: {new_token}")
        else:
            print(f" Using existing token: {order.Token_no}")
        
        order.updated_at = datetime.utcnow()
        order.updated_by = user_identifier 
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        print(f" Order picked successfully! Token: {order.Token_no}")
        return {
            "success": True,
            "message": "Order picked successfully", 
            "Token_no": order.Token_no,
            "order_id": order.order_id,
            "status": order.status
        }
        
    except Exception as e:
        db.rollback()
        print(f" Pick order error: {str(e)}")
        import traceback
        print(f" Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to pick order: {str(e)}")

@router.post("/{order_id}/complete")
def complete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Quick complete order"""
    try:
        user_identifier = get_user_identifier(current_user)

        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = OrderStatus.COMPLETED
        order.updated_at = datetime.utcnow()
        order.updated_by = user_identifier
        
        db.add(order)
        db.commit()
        
        return {"message": "Order completed successfully", "Token_no": order.Token_no}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete order: {str(e)}")


# @router.get("/dashboard/stats")
# def get_dashboard_stats(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """Get dashboard statistics for staff"""
#     try:
        
#         total_orders = db.exec(select(Order)).all()
        
        
#         pending_orders = db.exec(select(Order).where(Order.status == OrderStatus.PENDING)).all()
#         confirmed_orders = db.exec(select(Order).where(Order.status == OrderStatus.CONFIRMED)).all()
#         in_progress_orders = db.exec(select(Order).where(Order.status == OrderStatus.IN_PROGRESS)).all()
#         completed_orders = db.exec(select(Order).where(Order.status == OrderStatus.COMPLETED)).all()
        
#         return {
#             "total_orders": len(total_orders),
#             "pending_orders": len(pending_orders),
#             "confirmed_orders": len(confirmed_orders),
#             "in_progress_orders": len(in_progress_orders),
#             "completed_orders": len(completed_orders),
#             "today_orders": len([o for o in total_orders if o.created_at.date() == datetime.utcnow().date()])
#         }
        
#     except Exception as e:
#         print(f" Dashboard stats error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get dashboard statistics for staff"""
    try:
        print("Fetching dashboard statistics with all statuses")
        
        # Get all orders count
        total_orders = db.query(Order).count()
        
        # Get orders by each status
        pending_orders = db.query(Order).filter(Order.status == "pending").count()
        confirmed_orders = db.query(Order).filter(Order.status == "confirmed").count()
        picked_up_orders = db.query(Order).filter(Order.status == "picked_up").count()
        ready_to_pick_orders = db.query(Order).filter(Order.status == "ready").count()  # Assuming 'ready' means ready to pick
        in_progress_orders = db.query(Order).filter(Order.status == "in_progress").count()
        completed_orders = db.query(Order).filter(Order.status == "completed").count()
        delivered_orders = db.query(Order).filter(Order.status == "delivered").count()
        cancelled_orders = db.query(Order).filter(Order.status == "cancelled").count()
        rejected_orders = db.query(Order).filter(Order.status == "rejected").count()
        
        # Today's orders
        today = datetime.utcnow().date()
        today_orders = db.query(Order).filter(
            func.date(Order.created_at) == today
        ).count()
        
        # Calculate ready to pick (confirmed orders that are not picked up yet)
        # This is a business logic calculation
        ready_to_pick_calculated = confirmed_orders - picked_up_orders
        if ready_to_pick_calculated < 0:
            ready_to_pick_calculated = 0
        
        return {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "picked_up_orders": picked_up_orders,
            "ready_to_pick_orders": ready_to_pick_orders,  # Direct from database
            "ready_to_pick_calculated": ready_to_pick_calculated,  # Calculated (confirmed - picked_up)
            "in_progress_orders": in_progress_orders,
            "completed_orders": completed_orders,
            "delivered_orders": delivered_orders,
            "cancelled_orders": cancelled_orders,
            "rejected_orders": rejected_orders,
            "today_orders": today_orders
        }
        
    except Exception as e:
        print(f"Dashboard stats error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")