from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from models.order_item import OrderItemStatus, ServiceType, CategoryName, ProductName

class OrderItemBase(BaseModel):
    category_name: str
    product_name: str
    quantity: int 
    service: str
    status: Optional[OrderItemStatus] = OrderItemStatus.PROCESSED

    @field_validator('category_name')
    def validate_category_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Category name is required')
        
        v = v.strip()
        category_mapping = {
            'MENS_CLOTHING': "Men's Clothing",
            'WOMENS_CLOTHING': "Women's Clothing", 
            'KIDS_CLOTHING': "Kids Clothing",
            'HOUSE_HOLDS': "House Holds",
            'OTHERS': "Others"
        }
        return category_mapping.get(v, v)
    
    @field_validator('product_name') 
    def validate_product_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Product name is required')
        
        v = v.strip()
        product_mapping = {
            
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
        return product_mapping.get(v, v)
    
    model_config = {  
        "use_enum_values": True,
        "arbitrary_types_allowed": True
    }

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemUpdate(BaseModel):
    category_name: Optional[CategoryName] = None
    product_name: Optional[ProductName] = None
    quantity: Optional[int] = None
    service: Optional[ServiceType] = None
    status: Optional[OrderItemStatus] = None

    model_config = {
        "use_enum_values": True,
        "arbitrary_types_allowed": True
    }
    
class OrderItemResponse(OrderItemBase):
    order_item_id: int
    order_id: int
    status: OrderItemStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "use_enum_values": True,
        "arbitrary_types_allowed": True
    }