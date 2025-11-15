from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
import random
import string
from datetime import datetime

from db.session import get_db
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate, StaffOrderCreate
from dependencies.auth import get_current_user, get_current_staff_user
from models.user import User
from sqlalchemy.orm import selectinload
from models.address import Address

router = APIRouter()

#  ADD HELPER FUNCTIONS HERE (at the top level)
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
        "Men's Clothing": "Men's Clothing",  # Handle already correct values
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
        # Men's Clothing
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
        
        # Women's Clothing
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
        
        # Kids Clothing
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
        
        # House Holds
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
        
        # Others
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
    """Convert order status to valid enum values"""
    if not status:
        return OrderStatus.PENDING
    
    status_mapping = {
        'picked': OrderStatus.IN_PROGRESS,
        'PICKED': OrderStatus.IN_PROGRESS,
        'pending': OrderStatus.PENDING,
        'PENDING': OrderStatus.PENDING,
        'confirmed': OrderStatus.CONFIRMED,
        'CONFIRMED': OrderStatus.CONFIRMED,
        'in_progress': OrderStatus.IN_PROGRESS,
        'IN_PROGRESS': OrderStatus.IN_PROGRESS,
        'completed': OrderStatus.COMPLETED,
        'COMPLETED': OrderStatus.COMPLETED,
        'cancelled': OrderStatus.CANCELLED,
        'CANCELLED': OrderStatus.CANCELLED
    }
    return status_mapping.get(status, OrderStatus.PENDING)

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
        'pending': "wash_iron",  # Map invalid values to default
        'PENDING': "wash_iron",
    }
    return service_mapping.get(service, "wash_iron")

def generate_order_number():
    """Generate unique order number"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD{date_str}-{random_str}"

def generate_token():
    """Generate unique token like TK101"""
    return f"TK{random.randint(100, 999)}"


@router.post("/", response_model=OrderResponse)
def create_order(
    order_data: StaffOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Create a new order (Staff can create orders for any customer)"""
    try:
        print(f" NEW FILE - Staff creating order. Staff ID: {current_user.user_id}")
        
        # Generate order number and token
        token_no = generate_token()
        
        #  FIX: USE EXISTING CUSTOMER ONLY - NO NEW CUSTOMER CREATION
        # Use user ID 99 (python user)
        customer = db.get(User, 99)
        
        if not customer:
            # If user 99 doesn't exist, use current staff
            customer = current_user
        
        print(f" Using customer: {customer.name} (ID: {customer.user_id})")
        
        # Create address for the customer
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
        
        # Create order
        db_order = Order(
            user_id=customer.user_id,
            address_id=customer_address.address_id,
            Token_no=token_no,
            service=order_data.service,
            status=OrderStatus.PENDING,
            created_by=current_user.email,
            updated_by=current_user.email
        )
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        print(f"Order created: {db_order.Token_no}")
        
        #  FIX: MERGE DUPLICATE ITEMS BEFORE CREATING
        merged_items = {}
        if order_data.items:
            for item_data in order_data.items:
                key = f"{item_data.category_name}_{item_data.product_name}"
                if key in merged_items:
                    # If item already exists, increase quantity
                    merged_items[key].quantity += item_data.quantity
                else:
                    # New item, add to dictionary
                    merged_items[key] = item_data
        
        print(f" Original items: {len(order_data.items)}, Merged items: {len(merged_items)}")

        # Create order items from merged data
        created_items = []
        for key, item_data in merged_items.items():
            db_item = OrderItem(
                order_id=db_order.order_id,
                category_name=item_data.category_name,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                service=order_data.service
            )
            db.add(db_item)
            created_items.append(db_item)
            
            db.commit()
            
            for item in created_items:
                db.refresh(item)
        
        # Get user details
        user = db.get(User, db_order.user_id)
        address = db.get(Address, db_order.address_id)
        
        # Get order items
        order_items = db.exec(
            select(OrderItem).where(OrderItem.order_id == db_order.order_id)
        ).all()
        
        # Build items response
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
        
        # Build address details
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
        
        # Build complete response
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
            # Address fields
            "address_line1": order_data.address_line1,
            "address_line2": order_data.address_line2,
            "city": order_data.city,
            "state": order_data.state,
            "pincode": order_data.pincode,
            # "landmark": order_data.landmark,
            # User details
            "user_name": user.name if user else None,
            "user_mobile": user.mobile_no if user else None,
            # Relationships
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

#  FIX: GET ORDER WITHOUT RELATIONSHIP ISSUES
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get specific order by ID"""
    try:
        print(f"Getting order: {order_id}")
        
        # Get order
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        print(f"Order found - ID: {order.order_id}, service: {order.service}, status: {order.status}")
        
        #  FIX: MANUALLY LOAD RELATIONSHIPS
        # Get related data manually
        user = db.get(User, order.user_id)
        address = db.get(Address, order.address_id)
        
        # Get order items
        order_items = db.exec(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).all()
        
        # Build items response
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
        
        # Build address details
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

        # Build complete response
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
            # Address fields (use from address if available)
            "address_line1": address.address_line1 if address else "",
            "address_line2": address.address_line2 if address else "",
            "city": address.city if address else "",
            "state": address.state if address else "",
            "pincode": address.pincode if address else "",
            # "landmark": address.landmark if address else "",
            # User details
            "user_name": user.name if user else None,
            "user_mobile": user.mobile_no if user else None,
            # Relationships
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

#  FIX: GET ORDERS LIST
#  COMPLETELY FIXED GET ORDERS ENDPOINT
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
        
        # Status filter
        if status:
            valid_status = convert_order_status(status)
            statement = statement.where(Order.status == valid_status.value)
        
        # Search filter
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
                
                # Get related data
                user = db.get(User, order.user_id)
                address = db.get(Address, order.address_id)
                
                # Get order items
                order_items = db.exec(
                    select(OrderItem).where(OrderItem.order_id == order.order_id)
                ).all()
                
                # Convert order items
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
                
                # Build address details
                address_details = None
                if address:
                    address_details = {
                        "address_line1": address.address_line1,
                        "address_line2": address.address_line2,
                        "city": address.city,
                        "state": address.state,
                        "pincode": address.pincode
                    }
                
                # CRITICAL: CONVERT SERVICE AND STATUS SEPARATELY
                order_service = convert_service_type(order.service)
                order_status = convert_order_status(order.status)
                
                print(f"  Converted service: '{order_service}'")
                print(f"  Converted status: '{order_status.value}'")
                
                # Build response as dictionary
                response_dict = {
                    "order_id": order.order_id,
                    "user_id": order.user_id,
                    "address_id": order.address_id,
                    "Token_no": order.Token_no,
                    "service": order_service,  #  This should be a string like "wash_iron"
                    "status": order_status.value,  #  This should be a string like "pending"
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
                
                # Validate the data before creating OrderResponse
                print(f"  Final service for response: '{response_dict['service']}'")
                print(f"  Final status for response: '{response_dict['status']}'")
                
                # Create OrderResponse
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


# Add this for customers to view their own orders
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
        
        # Verify user exists
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        statement = select(Order).where(Order.user_id == user_id)
        
        if service:
            valid_service = convert_service_type(service)
            statement = statement.where(Order.service == valid_service)
            print(f"Filtering by service: {valid_service}")
            
        # Status filter
        if status:
            valid_status = convert_order_status(status)
            statement = statement.where(Order.status == valid_status.value)
        
        statement = statement.offset(skip).limit(limit).order_by(Order.created_at.desc())
        orders = db.exec(statement).all()
        
        print(f"Found {len(orders)} orders for user {user_id}")
        
        orders_response = []
        for order in orders:
            try:
                # Get related data
                user = db.get(User, order.user_id)
                address = db.get(Address, order.address_id)
                
                # Get order items
                order_items = db.exec(
                    select(OrderItem).where(OrderItem.order_id == order.order_id)
                ).all()
                
                # Convert order items
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
                
                # Build address details
                address_details = None
                if address:
                    address_details = {
                        "address_line1": address.address_line1,
                        "address_line2": address.address_line2,
                        "city": address.city,
                        "state": address.state,
                        "pincode": address.pincode
                    }
                
                # Convert service and status
                order_service = convert_service_type(order.service)
                order_status = convert_order_status(order.status)

                # Build response
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
                
                order_response = OrderResponse(**response_dict)
                orders_response.append(order_response)
                
            except Exception as order_error:
                print(f"Error processing order {order.order_id}: {str(order_error)}")
                continue
        
        return orders_response
        
    except Exception as e:
        print(f"Get user orders error: {str(e)}")
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

#  PUT /api/v1/staff/orders/{order_id} - Update order
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
        
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update fields
        update_data = order_update.dict(exclude_unset=True)

        # Convert status if provided
        if 'status' in update_data and update_data['status']:
            update_data['status'] = convert_order_status(update_data['status']).value
        
        # Convert service if provided  
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

        #  RETURN PROPERLY FORMATTED RESPONSE
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


#  DELETE /api/v1/staff/orders/{order_id} - Delete order
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
        
        # Delete associated order items first
        items_statement = select(OrderItem).where(OrderItem.order_id == order_id)
        order_items = db.exec(items_statement).all()
        for item in order_items:
            db.delete(item)
        
        # Delete order
        db.delete(order)
        db.commit()
        
        print(f" Order deleted: {order_id}")
        return {"message": "Order deleted successfully"}
        
    except Exception as e:
        db.rollback()
        print(f" Delete order error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete order: {str(e)}")

#  Quick action endpoints

@router.post("/{order_id}/confirm")
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Quick confirm order"""
    try:
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = OrderStatus.CONFIRMED
        order.updated_at = datetime.utcnow()
        order.updated_by = current_user.email
        
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
        
        # Get order with relationship
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        print(f" Order found - ID: {order.order_id}, Token: {order.Token_no}, Status: {order.status}")
        
        # Update order status to PICKED
        order.status = OrderStatus.PICKED
        
        # Generate token if not exists
        if not order.Token_no:
            new_token = generate_token()
            order.Token_no = new_token
            print(f" Generated new token: {new_token}")
        else:
            print(f" Using existing token: {order.Token_no}")
        
        order.updated_at = datetime.utcnow()
        order.updated_by = current_user.email
        
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
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = OrderStatus.COMPLETED
        order.updated_at = datetime.utcnow()
        order.updated_by = current_user.email
        
        db.add(order)
        db.commit()
        
        return {"message": "Order completed successfully", "Token_no": order.Token_no}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete order: {str(e)}")

#  Staff dashboard statistics
@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get dashboard statistics for staff"""
    try:
        # Total orders count
        total_orders = db.exec(select(Order)).all()
        
        # Orders by status
        pending_orders = db.exec(select(Order).where(Order.status == OrderStatus.PENDING)).all()
        confirmed_orders = db.exec(select(Order).where(Order.status == OrderStatus.CONFIRMED)).all()
        in_progress_orders = db.exec(select(Order).where(Order.status == OrderStatus.IN_PROGRESS)).all()
        completed_orders = db.exec(select(Order).where(Order.status == OrderStatus.COMPLETED)).all()
        
        return {
            "total_orders": len(total_orders),
            "pending_orders": len(pending_orders),
            "confirmed_orders": len(confirmed_orders),
            "in_progress_orders": len(in_progress_orders),
            "completed_orders": len(completed_orders),
            "today_orders": len([o for o in total_orders if o.created_at.date() == datetime.utcnow().date()])
        }
        
    except Exception as e:
        print(f" Dashboard stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")
