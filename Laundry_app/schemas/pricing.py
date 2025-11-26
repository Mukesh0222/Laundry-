# from typing import Optional
# from pydantic import BaseModel, validator
# from models.pricing import ServiceType, CategoryName, ProductName

# class PricingCreate(BaseModel):
#     service_type: ServiceType
#     category: CategoryName
#     product: ProductName
#     price: float

#     @validator('service_type', 'category', 'product', pre=True)
#     def convert_to_enum(cls, v):
#         if isinstance(v, str):
            
#             if hasattr(ServiceType, v.upper()):
#                 return getattr(ServiceType, v.upper())
            
#             for enum_class in [ServiceType, CategoryName, ProductName]:
#                 for member in enum_class:
#                     if member.value.lower() == v.lower():
#                         return member
#         return v
    
# class PricingUpdate(BaseModel):
#     service_type: Optional[ServiceType] = None
#     category: Optional[CategoryName] = None
#     product: Optional[ProductName] = None
#     price: Optional[float] = None

#     @validator('service_type', 'category', 'product', pre=True)
#     def convert_to_enum(cls, v):
#         if v is not None and isinstance(v, str):
            
#             if hasattr(ServiceType, v.upper()):
#                 return getattr(ServiceType, v.upper())
            
#             for enum_class in [ServiceType, CategoryName, ProductName]:
#                 for member in enum_class:
#                     if member.value.lower() == v.lower():
#                         return member
#         return v

# class PricingResponse(BaseModel):
#     id: int
#     service_type: ServiceType
#     category: CategoryName
#     product: ProductName
#     price: float
    
#     class Config:
#         from_attributes = True

# class PricingBulkCreate(BaseModel):
#     items: list[PricingCreate]

from typing import Optional, List
from pydantic import BaseModel, validator
from models.pricing import ServiceType, CategoryName, ProductName

class PricingCreate(BaseModel):
    service_type: str  # Changed from ServiceType to str
    category: str      # Changed from CategoryName to str  
    product: str       # Changed from ProductName to str
    price: float

    @validator('service_type', 'category', 'product')
    def validate_non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()

class PricingUpdate(BaseModel):
    service_type: Optional[str] = None
    category: Optional[str] = None  
    product: Optional[str] = None
    price: Optional[float] = None

    @validator('service_type', 'category', 'product')
    def validate_non_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('This field cannot be empty')
        return v.strip() if v else v

class PricingResponse(BaseModel):
    id: int
    service_type: str
    category: str
    product: str
    price: float
    
    class Config:
        from_attributes = True

class PricingBulkCreate(BaseModel):
    items: List[PricingCreate]

class DynamicEnumCreate(BaseModel):
    service_type: Optional[str] = None
    category: Optional[str] = None
    product: Optional[str] = None

class DynamicEnumResponse(BaseModel):
    service_types: List[str]
    categories: List[str]
    products: List[str]