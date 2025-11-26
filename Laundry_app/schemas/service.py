# schemas/service.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime

# ========== SERVICE SCHEMAS ==========

class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None

class ServiceCreate(ServiceBase):
    categories: Optional[List['ServiceCategoryCreate']] = []

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ServiceResponse(ServiceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  

# ========== CATEGORY SCHEMAS ==========

class ServiceCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class ServiceCategoryCreate(ServiceCategoryBase):
    products: Optional[List['ServiceProductCreate']] = []

class ServiceCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ServiceCategoryResponse(ServiceCategoryBase):
    id: int
    service_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Changed from orm_mode = True

# ========== PRODUCT SCHEMAS ==========

class ServiceProductBase(BaseModel):
    name: str
    price: float
    image_url: Optional[str] = None
    is_available: Optional[bool] = True

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

class ServiceProductCreate(ServiceProductBase):
    category_id: Optional[int] = None

class ServiceProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None

class ServiceProductResponse(ServiceProductBase):
    id: int
    category_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Changed from orm_mode = True

# ========== NESTED RELATIONSHIP SCHEMAS ==========

class ServiceProductWithDetails(ServiceProductBase):
    id: int
    category_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Changed from orm_mode = True

class ServiceCategoryWithFullProducts(ServiceCategoryBase):
    id: int
    service_id: int
    created_at: datetime
    updated_at: datetime
    products: List[ServiceProductWithDetails] = []  # Full product details

    class Config:
        from_attributes = True  # Changed from orm_mode = True

class ServiceWithFullDetails(ServiceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    categories: List[ServiceCategoryWithFullProducts] = []  # Full category details with products

    class Config:
        from_attributes = True  # Changed from orm_mode = True

# ========== SIMPLIFIED RESPONSE SCHEMAS ==========

class CategoryWithProductsResponse(BaseModel):
    category_name: str
    category_description: Optional[str] = None
    category_id: int
    products: List['ProductWithPriceResponse'] = []

    class Config:
        from_attributes = True  # Changed from orm_mode = True

class ProductWithPriceResponse(BaseModel):
    product_id: int
    product_name: str
    price: float
    image_url: Optional[str] = None
    is_available: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Changed from orm_mode = True

class ServiceWithCategoriesAndProductsResponse(BaseModel):
    service_id: int
    service_name: str
    service_description: Optional[str] = None
    categories: List[CategoryWithProductsResponse] = []

    class Config:
        from_attributes = True  # Changed from orm_mode = True

# ========== BULK OPERATION SCHEMAS ==========

class BulkCategoryCreate(BaseModel):
    categories: List[ServiceCategoryCreate]

class BulkProductCreate(BaseModel):
    products: List[ServiceProductCreate]

class BulkServiceCreate(BaseModel):
    service: ServiceBase
    categories: List[ServiceCategoryCreate]

class BulkOperationResponse(BaseModel):
    message: str
    created_count: int
    updated_count: int = 0
    failed_count: int = 0
    details: Optional[Dict[str, Any]] = None

class BulkUpdateResponse(BaseModel):
    message: str
    updated_count: int
    failed_count: int = 0
    details: Optional[Dict[str, Any]] = None

class BulkDeleteResponse(BaseModel):
    message: str
    deleted_count: int
    failed_count: int = 0

# ========== PRICE UPDATE SCHEMAS ==========

class PriceUpdate(BaseModel):
    new_price: float

    class Config:
        schema_extra = {"example": {"new_price": 99.99}}

class PriceUpdateResponse(BaseModel):
    message: str
    product_id: int
    old_price: float
    new_price: float

class BulkPriceUpdate(BaseModel):
    product_ids: List[int]
    new_price: float

class BulkPriceUpdateResponse(BaseModel):
    message: str
    updated_count: int
    failed_ids: List[int] = []

# Forward references
ServiceCreate.update_forward_refs()
ServiceCategoryCreate.update_forward_refs()
CategoryWithProductsResponse.update_forward_refs()