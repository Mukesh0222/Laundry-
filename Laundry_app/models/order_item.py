from sqlmodel import SQLModel, Field, Column, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy import UniqueConstraint, String

class OrderItemStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSED = "processed"
    WASHED = "washed"
    READY = "ready" 
    IRONED = "ironed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PICKED = "picked"
    REJECTED = "rejected"
    
    # CANCEL = "cancel"
    # DELETE = "delete"
    # PROCESSED = "processed"

class ServiceType(str, Enum):
    WASH_IRON = "wash_iron"
    DRY_CLEANING = "dry_cleaning"
    WASH_ONLY = "wash_only"
    IRON_ONLY = "iron_only"

class CategoryName(str, Enum):
    MENS_CLOTHING = "Men's Clothing"
    WOMENS_CLOTHING = "Women's Clothing"
    KIDS_CLOTHING = "Kids Clothing"
    HOUSE_HOLDS = "House Holds"
    OTHERS = "Others"

class ProductName(str, Enum):
    
    T_SHIRT = "T-Shirt"
    SHIRT = "Shirt"
    JEANS = "Jeans"
    TROUSERS = "Trousers"
    SHORTS = "Shorts"
    INNERWEAR = "Innerwear"
    FORMAL_SHIRT = "Formal Shirt"
    CASUAL_SHIRT = "Casual Shirt"
    JACKET = "Jacket"
    SWEATER = "Sweater"
    
    
    SAREE = "Saree"
    KURTI = "Kurti"
    DRESS = "Dress"
    BLOUSE = "Blouse"
    SKIRT = "Skirt"
    TOP = "Top"
    LEHENGA = "Lehenga"
    SALWAR = "Salwar"
    DUPATTA = "Dupatta"
    NIGHT_DRESS = "Night Dress"
    
    
    KIDS_TSHIRT = "Kids T-shirt"
    KIDS_SHORTS = "Kids Shorts"
    SCHOOL_UNIFORM = "School Uniform"
    FROCK = "Frock"
    PYJAMAS = "Pyjamas"
    KIDS_JEANS = "Kids Jeans"
    BABY_SUIT = "Baby Suit"
    ROMPER = "Romper"
    KIDS_JACKET = "Kids Jacket"
    KIDS_SWEATER = "Kids Sweater"
    
    
    BEDSHEET = "Bedsheet"
    PILLOW_COVER = "Pillow Cover"
    CURTAIN = "Curtain"
    TABLE_CLOTH = "Table Cloth"
    TOWEL = "Towel"
    BLANKET = "Blanket"
    CARPET = "Carpet"
    BED_COVER = "Bed Cover"
    CUSHION_COVER = "Cushion Cover"
    MATTRESS_COVER = "Mattress Cover"
    
    
    BAG = "Bag"
    CAP = "Cap"
    SCARF = "Scarf"
    GLOVES = "Gloves"
    SOCKS = "Socks"
    HANDKERCHIEF = "Handkerchief"
    BELT = "Belt"
    TIE = "Tie"
    STOLE = "Stole"
    MUFFLER = "Muffler"

# class OrderItem(SQLModel, table=True):
#     __tablename__ = "order_items"
    
#     order_item_id: Optional[int] = Field(default=None, primary_key=True)
#     order_id: int = Field(foreign_key="orders.order_id")
#     # category_name: str = Field(max_length=100)
#     # product_name: str = Field(max_length=150)
#     category_name: str = Field()
#     product_name: str = Field()
#     quantity: int = Field(default=1)
#     service: str = Field()
#     status: str = Field(sa_column=Column(String(250)))
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#     updated_at: datetime = Field(default_factory=datetime.utcnow)
#     created_by: Optional[str] = Field(default=None, max_length=150)
#     updated_by: Optional[str] = Field(default=None, max_length=150)

#     order: Optional["Order"] = Relationship(back_populates="items") 

    
#     __table_args__ = (
#         UniqueConstraint('order_id', 'category_name', 'product_name', name='uq_order_item'),
#     )


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    
    order_item_id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.order_id")
    category_name: str = Field(max_length=100)
    product_name: str = Field(max_length=100)
    quantity: int = Field(default=1)
    service: str = Field(max_length=50)
    status: str = Field(default="pending", max_length=50)
    unit_price: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(default=None, max_length=150)
    updated_by: Optional[str] = Field(default=None, max_length=150)
    
    # ✅ FIXED: Removed cascade_delete
    order: Optional["Order"] = Relationship(back_populates="items")