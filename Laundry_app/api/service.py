# routes.py - Complete merged version with ALL CRUD operations
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from typing import List, Optional

from db.session import get_db
from schemas.service import (
    ServiceCreate, ServiceResponse, ServiceUpdate,
    ServiceCategoryCreate, ServiceCategoryResponse, ServiceCategoryUpdate,
    ServiceProductCreate, ServiceProductResponse, ServiceProductUpdate,
    PriceUpdate, PriceUpdateResponse, BulkProductCreate, BulkOperationResponse,
    BulkCategoryCreate, BulkServiceCreate, BulkUpdateResponse, BulkDeleteResponse,
    BulkPriceUpdate, BulkPriceUpdateResponse, ServiceWithCategoriesAndProductsResponse, 
    CategoryWithProductsResponse, ProductWithPriceResponse
)
from crud.crud_service import ServiceCRUD, ServiceCategoryCRUD, ServiceProductCRUD
from models.service import Service, ServiceCategory, ServiceProduct

router = APIRouter()

# ========== SERVICE ROUTES ==========

@router.post("/services/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db)
):
    """Create a new service with categories"""
    service_dict = service_data.dict(exclude={'categories'})
    categories_data = service_data.categories
    
    service = ServiceCRUD.create_service_with_categories_and_products(
        db, service_dict, categories_data
    )
    
    service_response = ServiceResponse.from_orm(service)
    stats = ServiceCRUD.get_service_stats(db, service.id)
    
    service_response_dict = service_response.dict()
    service_response_dict.update(stats)
    
    return service_response_dict

@router.get("/services/{service_id}", response_model=ServiceResponse)
def get_service(
    service_id: int, 
    db: Session = Depends(get_db)
):
    """Get service by ID with details"""
    service = ServiceCRUD.get_service_with_details(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_response = ServiceResponse.from_orm(service)
    stats = ServiceCRUD.get_service_stats(db, service_id)
    
    service_response_dict = service_response.dict()
    service_response_dict.update(stats)
    
    return service_response_dict

@router.get("/services/", response_model=List[ServiceResponse])
def get_all_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all services with pagination"""
    services = ServiceCRUD.get_all_services(db, skip=skip, limit=limit)
    
    response_services = []
    for service in services:
        service_response = ServiceResponse.from_orm(service)
        stats = ServiceCRUD.get_service_stats(db, service.id)
        
        service_dict = service_response.dict()
        service_dict.update(stats)
        response_services.append(service_dict)
    
    return response_services

@router.put("/services/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db)
):
    """Update service details"""
    service = ServiceCRUD.update_service(db, service_id, service_data.dict(exclude_unset=True))
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_response = ServiceResponse.from_orm(service)
    stats = ServiceCRUD.get_service_stats(db, service_id)
    
    service_response_dict = service_response.dict()
    service_response_dict.update(stats)
    
    return service_response_dict

@router.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db)
):
    """Delete a service"""
    success = ServiceCRUD.delete_service(db, service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {"message": "Service deleted successfully"}

# ========== CATEGORY ROUTES ==========

@router.post("/services/{service_id}/categories/", response_model=ServiceCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    service_id: int,
    category_data: ServiceCategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new category in a service"""
    category = ServiceCategoryCRUD.create_category(db, service_id, category_data.dict())
    return ServiceCategoryResponse.from_orm(category)

@router.get("/services/{service_id}/categories/", response_model=List[ServiceCategoryResponse])
def get_service_categories(
    service_id: int, 
    db: Session = Depends(get_db)
):
    """Get all categories for a service"""
    categories = ServiceCategoryCRUD.get_categories_by_service(db, service_id)
    
    response_categories = []
    for category in categories:
        category_response = ServiceCategoryResponse.from_orm(category)
        category_dict = category_response.dict()
        category_dict['products_count'] = len(category.products)
        response_categories.append(category_dict)
    
    return response_categories

@router.get("/categories/{category_id}", response_model=ServiceCategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Get category by ID"""
    category = ServiceCategoryCRUD.get_category_with_products(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category_response = ServiceCategoryResponse.from_orm(category)
    category_dict = category_response.dict()
    category_dict['products_count'] = len(category.products)
    return category_dict

@router.put("/categories/{category_id}", response_model=ServiceCategoryResponse)
def update_category(
    category_id: int,
    category_data: ServiceCategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update category details"""
    category = ServiceCategoryCRUD.update_category(db, category_id, category_data.dict(exclude_unset=True))
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return ServiceCategoryResponse.from_orm(category)

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Delete a category"""
    success = ServiceCategoryCRUD.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Category deleted successfully"}

# ========== PRODUCT ROUTES ==========

@router.post("/categories/{category_id}/products/", response_model=ServiceProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    category_id: int,
    product_data: ServiceProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product in a category"""
    # Verify category exists
    category = ServiceCategoryCRUD.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    product_dict = product_data.dict()
    product_dict['category_id'] = category_id
    
    product = ServiceProductCRUD.create_product(db, product_dict)
    return ServiceProductResponse.from_orm(product)

@router.post("/services/{service_id}/categories/{category_id}/products/", response_model=ServiceProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_with_verification(
    service_id: int,
    category_id: int,
    product_data: ServiceProductCreate,
    db: Session = Depends(get_db)
):
    """Create product with service and category verification"""
    # Verify both service and category exist and are linked
    service = ServiceCRUD.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    category = ServiceCategoryCRUD.get_category(db, category_id)
    if not category or category.service_id != service_id:
        raise HTTPException(status_code=404, detail="Category not found in this service")
    
    product_dict = product_data.dict()
    product_dict['category_id'] = category_id
    
    product = ServiceProductCRUD.create_product(db, product_dict)
    return ServiceProductResponse.from_orm(product)

@router.get("/categories/{category_id}/products/", response_model=List[ServiceProductResponse])
def get_category_products(
    category_id: int, 
    db: Session = Depends(get_db)
):
    """Get all products in a category"""
    products = ServiceProductCRUD.get_products_by_category(db, category_id)
    return [ServiceProductResponse.from_orm(product) for product in products]

@router.get("/services/{service_id}/products/", response_model=List[ServiceProductResponse])
def get_service_products(
    service_id: int,
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all products in a service, optionally filtered by category"""
    products = ServiceProductCRUD.get_products_by_service(db, service_id, category_id)
    return [ServiceProductResponse.from_orm(product) for product in products]

@router.get("/products/{product_id}", response_model=ServiceProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get product by ID"""
    product = ServiceProductCRUD.get_product_with_details(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ServiceProductResponse.from_orm(product)

@router.put("/products/{product_id}", response_model=ServiceProductResponse)
def update_product(
    product_id: int,
    product_data: ServiceProductUpdate,
    db: Session = Depends(get_db)
):
    """Update product details"""
    product = ServiceProductCRUD.update_product(db, product_id, product_data.dict(exclude_unset=True))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ServiceProductResponse.from_orm(product)

@router.put("/products/{product_id}/price", response_model=PriceUpdateResponse)
def update_product_price(
    product_id: int,
    price_data: PriceUpdate,
    db: Session = Depends(get_db)
):
    """Update product price only"""
    product = ServiceProductCRUD.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    old_price = product.price
    updated_product = ServiceProductCRUD.update_product_price(db, product_id, price_data.new_price)
    
    return PriceUpdateResponse(
        message="Price updated successfully",
        product_id=product_id,
        old_price=old_price,
        new_price=updated_product.price
    )

@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Delete a product"""
    success = ServiceProductCRUD.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}

# ========== BULK OPERATIONS ==========

@router.post("/services/{service_id}/products/bulk/", response_model=BulkOperationResponse, status_code=status.HTTP_201_CREATED)
def create_bulk_products(
    service_id: int,
    bulk_data: BulkProductCreate,
    db: Session = Depends(get_db)
):
    """Create multiple products in a service"""
    service = ServiceCRUD.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    created_count = 0
    failed_count = 0
    details = {"products": [], "failed": []}
    
    for product_data in bulk_data.products:
        try:
            product_dict = product_data.dict()
            
            if not product_dict.get('category_id'):
                default_category = ServiceCategoryCRUD.get_or_create_default_category(db, service_id)
                product_dict['category_id'] = default_category.id
            else:
                # Verify category belongs to service
                category = ServiceCategoryCRUD.get_category(db, product_dict['category_id'])
                if not category or category.service_id != service_id:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Category {product_dict['category_id']} not found in service"
                    )
            
            product = ServiceProductCRUD.create_product(db, product_dict)
            details["products"].append({
                "id": product.id,
                "name": product.name,
                "price": product.price
            })
            created_count += 1
        except Exception as e:
            failed_count += 1
            details["failed"].append({
                "name": product_data.name,
                "error": str(e)
            })
    
    return BulkOperationResponse(
        message=f"Successfully created {created_count} products",
        created_count=created_count,
        failed_count=failed_count,
        details=details
    )

@router.delete("/services/{service_id}/categories/")
def delete_all_categories(
    service_id: int,
    db: Session = Depends(get_db)
):
    """Delete all categories in a service"""
    success = ServiceCategoryCRUD.delete_all_categories_in_service(db, service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found or no categories to delete")
    
    return {"message": "All categories deleted successfully"}

# ========== SIMPLIFIED DETAILS ROUTES ==========

@router.get("/services/{service_id}/full-details", response_model=ServiceWithCategoriesAndProductsResponse)
def get_service_full_details(service_id: int, db: Session = Depends(get_db)):
    """Get service with all categories and their products (without counts)"""
    service = ServiceCRUD.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Get all categories for this service
    categories = ServiceCategoryCRUD.get_categories_by_service(db, service_id)
    
    categories_with_products = []
    for category in categories:
        # Get all products for this category
        products = ServiceProductCRUD.get_products_by_category(db, category.id)
        
        # Convert products to simplified response
        product_responses = []
        for product in products:
            product_responses.append(ProductWithPriceResponse(
                product_id=product.id,
                product_name=product.name,
                price=product.price,
                image_url=product.image_url,
                is_available=product.is_available,
                created_at=product.created_at
            ))
        
        # Create category with products response
        category_response = CategoryWithProductsResponse(
            category_name=category.name,
            category_description=category.description,
            category_id=category.id,
            products=product_responses
        )
        categories_with_products.append(category_response)
    
    return ServiceWithCategoriesAndProductsResponse(
        service_id=service.id,
        service_name=service.name,
        service_description=service.description,
        categories=categories_with_products
    )

@router.get("/services/{service_id}/categories-with-products", response_model=List[CategoryWithProductsResponse])
def get_service_categories_with_products(service_id: int, db: Session = Depends(get_db)):
    """Get all categories with their products for a service"""
    categories = ServiceCategoryCRUD.get_categories_by_service(db, service_id)
    
    categories_with_products = []
    for category in categories:
        products = ServiceProductCRUD.get_products_by_category(db, category.id)
        
        product_responses = []
        for product in products:
            product_responses.append(ProductWithPriceResponse(
                product_id=product.id,
                product_name=product.name,
                price=product.price,
                image_url=product.image_url,
                is_available=product.is_available,
                created_at=product.created_at
            ))
        
        category_response = CategoryWithProductsResponse(
            category_name=category.name,
            category_description=category.description,
            category_id=category.id,
            products=product_responses
        )
        categories_with_products.append(category_response)
    
    return categories_with_products

@router.get("/categories/{category_id}/products-with-details", response_model=CategoryWithProductsResponse)
def get_category_with_products(category_id: int, db: Session = Depends(get_db)):
    """Get a specific category with all its products"""
    category = ServiceCategoryCRUD.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    products = ServiceProductCRUD.get_products_by_category(db, category_id)
    
    product_responses = []
    for product in products:
        product_responses.append(ProductWithPriceResponse(
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            image_url=product.image_url,
            is_available=product.is_available,
            created_at=product.created_at
        ))
    
    return CategoryWithProductsResponse(
        category_name=category.name,
        category_description=category.description,
        category_id=category.id,
        products=product_responses
    )

@router.get("/all-services-with-details", response_model=List[ServiceWithCategoriesAndProductsResponse])
def get_all_services_with_full_details(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all services with their categories and products"""
    services = ServiceCRUD.get_all_services(db, skip=skip, limit=limit)
    
    result = []
    for service in services:
        categories = ServiceCategoryCRUD.get_categories_by_service(db, service.id)
        
        categories_with_products = []
        for category in categories:
            products = ServiceProductCRUD.get_products_by_category(db, category.id)
            
            product_responses = []
            for product in products:
                product_responses.append(ProductWithPriceResponse(
                    product_id=product.id,
                    product_name=product.name,
                    price=product.price,
                    image_url=product.image_url,
                    is_available=product.is_available,
                    created_at=product.created_at
                ))
            
            category_response = CategoryWithProductsResponse(
                category_name=category.name,
                category_description=category.description,
                category_id=category.id,
                products=product_responses
            )
            categories_with_products.append(category_response)
        
        service_response = ServiceWithCategoriesAndProductsResponse(
            service_id=service.id,
            service_name=service.name,
            service_description=service.description,
            categories=categories_with_products
        )
        result.append(service_response)
    
    return result

@router.get("/products/with-prices", response_model=List[ProductWithPriceResponse])
def get_all_products_with_prices(
    service_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all products with their prices (filterable by service/category)"""
    if service_id:
        products = ServiceProductCRUD.get_products_by_service(db, service_id, category_id)
    elif category_id:
        products = ServiceProductCRUD.get_products_by_category(db, category_id)
    else:
        products = ServiceProductCRUD.get_all_products(db)
    
    result = []
    for product in products:
        result.append(ProductWithPriceResponse(
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            image_url=product.image_url,
            is_available=product.is_available,
            created_at=product.created_at
        ))
    
    return result

# ========== ADDITIONAL BULK OPERATIONS ==========

@router.post("/services/bulk/", response_model=BulkOperationResponse, status_code=status.HTTP_201_CREATED)
def create_bulk_services(
    bulk_data: List[ServiceCreate],
    db: Session = Depends(get_db)
):
    """Create multiple services with their categories and products"""
    created_count = 0
    failed_count = 0
    details = {"services": [], "failed": []}
    
    for service_data in bulk_data:
        try:
            service_dict = service_data.dict(exclude={'categories'})
            categories_data = service_data.categories
            
            service = ServiceCRUD.create_service_with_categories_and_products(
                db, service_dict, categories_data
            )
            
            details["services"].append({
                "id": service.id,
                "name": service.name,
                "categories_count": len(categories_data)
            })
            created_count += 1
        except Exception as e:
            failed_count += 1
            details["failed"].append({
                "name": service_data.name,
                "error": str(e)
            })
    
    return BulkOperationResponse(
        message=f"Successfully created {created_count} services",
        created_count=created_count,
        failed_count=failed_count,
        details=details
    )

@router.post("/services/{service_id}/categories/bulk/", response_model=BulkOperationResponse, status_code=status.HTTP_201_CREATED)
def create_bulk_categories(
    service_id: int,
    bulk_data: BulkCategoryCreate,
    db: Session = Depends(get_db)
):
    """Create multiple categories in a service with their products"""
    service = ServiceCRUD.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    created_count = 0
    failed_count = 0
    details = {"categories": [], "failed": []}
    
    for category_data in bulk_data.categories:
        try:
            category = ServiceCategoryCRUD.create_category_with_products(
                db, service_id, category_data.dict()
            )
            
            details["categories"].append({
                "id": category.id,
                "name": category.name,
                "products_count": len(category_data.products) if category_data.products else 0
            })
            created_count += 1
        except Exception as e:
            failed_count += 1
            details["failed"].append({
                "name": category_data.name,
                "error": str(e)
            })
    
    return BulkOperationResponse(
        message=f"Successfully created {created_count} categories in service",
        created_count=created_count,
        failed_count=failed_count,
        details=details
    )

@router.post("/categories/{category_id}/products/bulk/", response_model=BulkOperationResponse, status_code=status.HTTP_201_CREATED)
def create_bulk_products_in_category(
    category_id: int,
    bulk_data: BulkProductCreate,
    db: Session = Depends(get_db)
):
    """Create multiple products in a category"""
    category = ServiceCategoryCRUD.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    created_count = 0
    failed_count = 0
    details = {"products": [], "failed": []}
    
    for product_data in bulk_data.products:
        try:
            product_dict = product_data.dict()
            product_dict['category_id'] = category_id
            
            product = ServiceProductCRUD.create_product(db, product_dict)
            
            details["products"].append({
                "id": product.id,
                "name": product.name,
                "price": product.price
            })
            created_count += 1
        except Exception as e:
            failed_count += 1
            details["failed"].append({
                "name": product_data.name,
                "error": str(e)
            })
    
    return BulkOperationResponse(
        message=f"Successfully created {created_count} products",
        created_count=created_count,
        failed_count=failed_count,
        details=details
    )

@router.put("/products/bulk/price", response_model=BulkPriceUpdateResponse)
def bulk_update_product_prices(
    bulk_data: BulkPriceUpdate,
    db: Session = Depends(get_db)
):
    """Update prices for multiple products at once"""
    updated_count = 0
    failed_ids = []
    
    for product_id in bulk_data.product_ids:
        try:
            product = ServiceProductCRUD.update_product_price(db, product_id, bulk_data.new_price)
            if product:
                updated_count += 1
            else:
                failed_ids.append(product_id)
        except Exception:
            failed_ids.append(product_id)
    
    return BulkPriceUpdateResponse(
        message=f"Updated prices for {updated_count} products",
        updated_count=updated_count,
        failed_ids=failed_ids
    )

@router.delete("/services/bulk/", response_model=BulkDeleteResponse)
def bulk_delete_services(
    service_ids: List[int] = Query(...),
    db: Session = Depends(get_db)
):
    """Delete multiple services"""
    deleted_count = 0
    failed_ids = []
    
    for service_id in service_ids:
        try:
            success = ServiceCRUD.delete_service(db, service_id)
            if success:
                deleted_count += 1
            else:
                failed_ids.append(service_id)
        except Exception:
            failed_ids.append(service_id)
    
    return BulkDeleteResponse(
        message=f"Deleted {deleted_count} services",
        deleted_count=deleted_count,
        failed_ids=failed_ids
    )

@router.delete("/categories/bulk/", response_model=BulkDeleteResponse)
def bulk_delete_categories(
    category_ids: List[int] = Query(...),
    db: Session = Depends(get_db)
):
    """Delete multiple categories"""
    deleted_count = 0
    failed_ids = []
    
    for category_id in category_ids:
        try:
            success = ServiceCategoryCRUD.delete_category(db, category_id)
            if success:
                deleted_count += 1
            else:
                failed_ids.append(category_id)
        except Exception:
            failed_ids.append(category_id)
    
    return BulkDeleteResponse(
        message=f"Deleted {deleted_count} categories",
        deleted_count=deleted_count,
        failed_ids=failed_ids
    )

@router.delete("/products/bulk/", response_model=BulkDeleteResponse)
def bulk_delete_products(
    product_ids: List[int] = Query(...),
    db: Session = Depends(get_db)
):
    """Delete multiple products"""
    deleted_count = 0
    failed_ids = []
    
    for product_id in product_ids:
        try:
            success = ServiceProductCRUD.delete_product(db, product_id)
            if success:
                deleted_count += 1
            else:
                failed_ids.append(product_id)
        except Exception:
            failed_ids.append(product_id)
    
    return BulkDeleteResponse(
        message=f"Deleted {deleted_count} products",
        deleted_count=deleted_count,
        failed_ids=failed_ids
    )