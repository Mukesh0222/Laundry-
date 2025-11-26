from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from sqlalchemy import text

from db.session import get_db
from models.pricing import Pricing, ServiceType, CategoryName, ProductName
from schemas.pricing import PricingCreate, PricingUpdate, PricingResponse, PricingBulkCreate, DynamicEnumCreate, DynamicEnumResponse
from dependencies.auth import get_current_staff_user
from models.user import User

router = APIRouter(prefix="/pricing", tags=["pricing"])

class DynamicEnumManager:
    """Manage dynamic enum values in database"""
    
    @staticmethod
    def get_all_service_types(db: Session) -> List[str]:
        """Get all service types from database"""
        try:
            result = db.execute(text("SELECT DISTINCT service_type FROM pricing")).fetchall()
            db_values = [row[0] for row in result]
            enum_values = [st.value for st in ServiceType]
            return list(set(db_values + enum_values))
        except Exception as e:
            print(f"Error getting service types: {e}")
            return [st.value for st in ServiceType]
    
    @staticmethod
    def get_all_categories(db: Session) -> List[str]:
        """Get all categories from database"""
        try:
            result = db.execute(text("SELECT DISTINCT category FROM pricing")).fetchall()
            db_values = [row[0] for row in result]
            enum_values = [cat.value for cat in CategoryName]
            return list(set(db_values + enum_values))
        except Exception as e:
            print(f"Error getting categories: {e}")
            return [cat.value for cat in CategoryName]
    
    @staticmethod
    def get_all_products(db: Session) -> List[str]:
        """Get all products from database"""
        try:
            result = db.execute(text("SELECT DISTINCT product FROM pricing")).fetchall()
            db_values = [row[0] for row in result]
            enum_values = [prod.value for prod in ProductName]
            return list(set(db_values + enum_values))
        except Exception as e:
            print(f"Error getting products: {e}")
            return [prod.value for prod in ProductName]

@router.post("/", response_model=PricingResponse, status_code=status.HTTP_201_CREATED)
def create_pricing(
    pricing_data: PricingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Create a new pricing record - accepts dynamic service, category, product"""
    try:
        print(f"Creating pricing with: {pricing_data.dict()}")
        
        # Validate input lengths
        if len(pricing_data.service_type) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service type too long (max 100 characters)"
            )
        
        if len(pricing_data.category) > 150:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category too long (max 150 characters)"
            )
        
        if len(pricing_data.product) > 150:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product too long (max 150 characters)"
            )
        
        # Check if combination already exists
        existing = db.exec(
            select(Pricing).where(
                Pricing.service_type == pricing_data.service_type,
                Pricing.category == pricing_data.category,
                Pricing.product == pricing_data.product
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pricing record with this service type, category, and product combination already exists"
            )
        
        pricing = Pricing(**pricing_data.dict())
        db.add(pricing)
        db.commit()
        db.refresh(pricing)
        
        print(f"Pricing created successfully: {pricing.id}")
        return pricing
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error creating pricing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pricing record: {str(e)}"
        )

@router.post("/bulk", response_model=List[PricingResponse], status_code=status.HTTP_201_CREATED)
def create_bulk_pricing(
    bulk_data: PricingBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Create multiple pricing records at once"""
    created_items = []
    
    for item in bulk_data.items:
        # Validate lengths
        if len(item.service_type) > 100 or len(item.category) > 150 or len(item.product) > 150:
            continue  # Skip invalid items
            
        # Check if combination already exists
        existing = db.exec(
            select(Pricing).where(
                Pricing.service_type == item.service_type,
                Pricing.category == item.category,
                Pricing.product == item.product
            )
        ).first()
        
        if not existing:
            pricing = Pricing(**item.dict())
            db.add(pricing)
            created_items.append(pricing)
    
    db.commit()
    
    # Refresh all created items
    for item in created_items:
        db.refresh(item)
    
    return created_items

@router.get("/", response_model=List[PricingResponse])
def get_all_pricing(
    skip: int = 0,
    limit: int = 100,
    service_type: Optional[str] = None,
    category: Optional[str] = None,
    product: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all pricing records with optional filtering"""
    query = select(Pricing)
    
    if service_type:
        query = query.where(Pricing.service_type == service_type)
    if category:
        query = query.where(Pricing.category == category)
    if product:
        query = query.where(Pricing.product == product)
    
    pricing = db.exec(query.offset(skip).limit(limit)).all()
    return pricing

@router.get("/{pricing_id}", response_model=PricingResponse)
def get_pricing(
    pricing_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific pricing record by ID"""
    pricing = db.get(Pricing, pricing_id)
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing record not found"
        )
    return pricing

@router.get("/lookup/price", response_model=PricingResponse)
def lookup_price(
    service_type: str,
    category: str,
    product: str,
    db: Session = Depends(get_db)
):
    """Look up price by service type, category, and product"""
    pricing = db.exec(
        select(Pricing).where(
            Pricing.service_type == service_type,
            Pricing.category == category,
            Pricing.product == product
        )
    ).first()
    
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pricing record found for the specified combination"
        )
    
    return pricing

@router.put("/{pricing_id}", response_model=PricingResponse)
def update_pricing(
    pricing_id: int,
    pricing_update: PricingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update a pricing record"""
    pricing = db.get(Pricing, pricing_id)
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing record not found"
        )
    
    # Validate lengths for updated fields
    if pricing_update.service_type and len(pricing_update.service_type) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service type too long (max 100 characters)"
        )
    
    if pricing_update.category and len(pricing_update.category) > 150:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category too long (max 150 characters)"
        )
    
    if pricing_update.product and len(pricing_update.product) > 150:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product too long (max 150 characters)"
        )
    
    # Check if the update would create a duplicate
    if pricing_update.service_type or pricing_update.category or pricing_update.product:
        new_service_type = pricing_update.service_type or pricing.service_type
        new_category = pricing_update.category or pricing.category
        new_product = pricing_update.product or pricing.product
        
        existing = db.exec(
            select(Pricing).where(
                Pricing.service_type == new_service_type,
                Pricing.category == new_category,
                Pricing.product == new_product,
                Pricing.id != pricing_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another pricing record with this combination already exists"
            )
    
    # Update fields
    update_data = pricing_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pricing, field, value)
    
    db.add(pricing)
    db.commit()
    db.refresh(pricing)
    return pricing

@router.delete("/{pricing_id}")
def delete_pricing(
    pricing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Delete a pricing record"""
    pricing = db.get(Pricing, pricing_id)
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing record not found"
        )
    
    db.delete(pricing)
    db.commit()
    return {"message": "Pricing record deleted successfully"}

# NEW ENDPOINTS FOR DYNAMIC ENUMS

@router.get("/enums/options", response_model=DynamicEnumResponse)
def get_enum_options(db: Session = Depends(get_db)):
    """Get all available enum options from database (dynamic + predefined)"""
    service_types = DynamicEnumManager.get_all_service_types(db)
    categories = DynamicEnumManager.get_all_categories(db)
    products = DynamicEnumManager.get_all_products(db)
    
    return DynamicEnumResponse(
        service_types=sorted(list(set(service_types))),
        categories=sorted(list(set(categories))),
        products=sorted(list(set(products)))
    )

@router.post("/enums/add", status_code=status.HTTP_201_CREATED)
def add_enum_option(
    enum_data: DynamicEnumCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Add new enum options dynamically"""
    added_items = []
    
    if enum_data.service_type:
        if len(enum_data.service_type) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service type too long (max 100 characters)"
            )
        added_items.append(f"Service Type: {enum_data.service_type}")
    
    if enum_data.category:
        if len(enum_data.category) > 150:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category too long (max 150 characters)"
            )
        added_items.append(f"Category: {enum_data.category}")
    
    if enum_data.product:
        if len(enum_data.product) > 150:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product too long (max 150 characters)"
            )
        added_items.append(f"Product: {enum_data.product}")
    
    if not added_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one enum value must be provided"
        )
    
    return {
        "message": "Enum options added successfully",
        "added_items": added_items,
        "note": "These values will now be available when creating new pricing records"
    }

@router.get("/enums/unique-values")
def get_unique_values(
    field: str = Query(..., description="Field name: service_type, category, or product"),
    db: Session = Depends(get_db)
):
    """Get unique values for a specific field"""
    if field not in ["service_type", "category", "product"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field must be one of: service_type, category, product"
        )
    
    if field == "service_type":
        values = DynamicEnumManager.get_all_service_types(db)
    elif field == "category":
        values = DynamicEnumManager.get_all_categories(db)
    else:  # product
        values = DynamicEnumManager.get_all_products(db)
    
    return {
        "field": field,
        "values": sorted(list(set(values)))
    }