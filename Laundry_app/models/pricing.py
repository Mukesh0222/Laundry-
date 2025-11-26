# from sqlmodel import SQLModel, Field, Column, Enum
# from enum import Enum as PyEnum
# from typing import Optional,  Any
# from sqlalchemy import Enum, String, Text
# import json

# class CaseInsensitiveEnum(PyEnum):
#     @classmethod
#     def _missing_(cls, value: Any):
#         if isinstance(value, str):
            
#             for member in cls:
#                 if member.value.lower() == value.lower():
#                     return member
#         return None
    
# class ServiceType(str, PyEnum):
#     WASH_IRON = "wash_iron"
#     DRY_CLEANING = "dry_cleaning"
#     WASH_ONLY = "wash_only"
#     IRON_ONLY = "iron_only"

# class CategoryName(str, PyEnum):
#     MENS_CLOTHING = "Men's Clothing"
#     WOMENS_CLOTHING = "Women's Clothing"
#     KIDS_CLOTHING = "Kids Clothing"
#     HOUSE_HOLDS = "House Holds"
#     OTHERS = "Others"

# class ProductName(str, PyEnum):
    
#     T_SHIRT = "T-Shirt"
#     SHIRT = "Shirt"
#     JEANS = "Jeans"
#     TROUSERS = "Trousers"
#     SHORTS = "Shorts"
#     INNERWEAR = "Innerwear"
#     FORMAL_SHIRT = "Formal Shirt"
#     CASUAL_SHIRT = "Casual Shirt"
#     JACKET = "Jacket"
#     SWEATER = "Sweater"
    
    
#     SAREE = "Saree"
#     KURTI = "Kurti"
#     DRESS = "Dress"
#     BLOUSE = "Blouse"
#     SKIRT = "Skirt"
#     TOP = "Top"
#     LEHENGA = "Lehenga"
#     SALWAR = "Salwar"
#     DUPATTA = "Dupatta"
#     NIGHT_DRESS = "Night Dress"
    
    
#     KIDS_TSHIRT = "Kids T-shirt"
#     KIDS_SHORTS = "Kids Shorts"
#     SCHOOL_UNIFORM = "School Uniform"
#     FROCK = "Frock"
#     PYJAMAS = "Pyjamas"
#     KIDS_JEANS = "Kids Jeans"
#     BABY_SUIT = "Baby Suit"
#     ROMPER = "Romper"
#     KIDS_JACKET = "Kids Jacket"
#     KIDS_SWEATER = "Kids Sweater"
    
   
#     BEDSHEET = "Bedsheet"
#     PILLOW_COVER = "Pillow Cover"
#     CURTAIN = "Curtain"
#     TABLE_CLOTH = "Table Cloth"
#     TOWEL = "Towel"
#     BLANKET = "Blanket"
#     CARPET = "Carpet"
#     BED_COVER = "Bed Cover"
#     CUSHION_COVER = "Cushion Cover"
#     MATTRESS_COVER = "Mattress Cover"
    
   
#     BAG = "Bag"
#     CAP = "Cap"
#     SCARF = "Scarf"
#     GLOVES = "Gloves"
#     SOCKS = "Socks"
#     HANDKERCHIEF = "Handkerchief"
#     BELT = "Belt"
#     TIE = "Tie"
#     STOLE = "Stole"
#     MUFFLER = "Muffler"

# class Pricing(SQLModel, table=True):
#     __tablename__ = "pricing"
    
#     id: Optional[int] = Field(default=None, primary_key=True)
#     service_type: ServiceType = Field(sa_column=Column(Enum(ServiceType)))
#     category: CategoryName = Field(sa_column=Column(Enum(CategoryName)))
#     product: ProductName = Field(sa_column=Column(Enum(ProductName)))
#     price: float = Field(gt=0, description="Price must be greater than 0")
    
#     class Config:
#         unique_together = ["service_type", "category", "product"]


from sqlmodel import SQLModel, Field, Column, Session
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import Enum, String, Text
import json

# Dynamic enums that can be extended
class ServiceType(str, PyEnum):
    WASH_IRON = "wash_iron"
    DRY_CLEANING = "dry_cleaning"
    WASH_ONLY = "wash_only"
    IRON_ONLY = "iron_only"

class CategoryName(str, PyEnum):
    MENS_CLOTHING = "Men's Clothing"
    WOMENS_CLOTHING = "Women's Clothing"
    KIDS_CLOTHING = "Kids Clothing"
    HOUSE_HOLDS = "House Holds"
    OTHERS = "Others"

class ProductName(str, PyEnum):
    # Men's Clothing
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
    
    # Women's Clothing
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
    
    # Kids Clothing
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
    
    # House Holds
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
    
    # Others
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

class DynamicEnumManager(SQLModel):
    """Manage dynamic enum values in database"""
    
    @classmethod
    def get_all_service_types(cls, db: Session) -> List[str]:
        """Get all service types from database"""
        result = db.execute("SELECT DISTINCT service_type FROM pricing").fetchall()
        return [row[0] for row in result] + [st.value for st in ServiceType]
    
    @classmethod
    def get_all_categories(cls, db: Session) -> List[str]:
        """Get all categories from database"""
        result = db.execute("SELECT DISTINCT category FROM pricing").fetchall()
        return [row[0] for row in result] + [cat.value for cat in CategoryName]
    
    @classmethod
    def get_all_products(cls, db: Session) -> List[str]:
        """Get all products from database"""
        result = db.execute("SELECT DISTINCT product FROM pricing").fetchall()
        return [row[0] for row in result] + [prod.value for prod in ProductName]

class Pricing(SQLModel, table=True):
    __tablename__ = "pricing"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    service_type: str = Field(sa_column=Column(String(100)))  # Changed to String for dynamic values
    category: str = Field(sa_column=Column(String(150)))     # Changed to String for dynamic values
    product: str = Field(sa_column=Column(String(150)))      # Changed to String for dynamic values
    price: float = Field(gt=0, description="Price must be greater than 0")
    
    class Config:
        unique_together = ["service_type", "category", "product"]