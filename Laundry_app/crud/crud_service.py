# crud/crud_service.py
from sqlmodel import Session, select
from typing import List, Optional
from models.service import Service, ServiceCategory, ServiceProduct

class ServiceCRUD:
    @staticmethod
    def get_all_services(db: Session, skip: int = 0, limit: int = 100):
        # Use db.query() instead of db.exec()
        statement = select(Service).offset(skip).limit(limit)
        result = db.execute(statement)
        return result.scalars().all()
    
    @staticmethod
    def get_service(db: Session, service_id: int):
        statement = select(Service).where(Service.id == service_id)
        result = db.execute(statement)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_service_with_details(db: Session, service_id: int):
        statement = select(Service).where(Service.id == service_id)
        result = db.execute(statement)
        service = result.scalar_one_or_none()
        
        if service:
            # Get categories for this service
            categories_stmt = select(ServiceCategory).where(ServiceCategory.service_id == service_id)
            categories_result = db.execute(categories_stmt)
            service.categories = categories_result.scalars().all()
            
            # Get products for each category
            for category in service.categories:
                products_stmt = select(ServiceProduct).where(ServiceProduct.category_id == category.id)
                products_result = db.execute(products_stmt)
                category.products = products_result.scalars().all()
        
        return service
    
    @staticmethod
    def create_service(db: Session, service_data: dict):
        service = Service(**service_data)
        db.add(service)
        db.commit()
        db.refresh(service)
        return service
    
    @staticmethod
    def create_service_with_categories_and_products(db: Session, service_data: dict, categories_data: list):
        # Create service
        service = Service(**service_data)
        db.add(service)
        db.commit()
        db.refresh(service)
        
        # Create categories and products
        for category_data in categories_data:
            category_products = category_data.pop('products', [])
            
            # Create category
            category = ServiceCategory(**category_data, service_id=service.id)
            db.add(category)
            db.commit()
            db.refresh(category)
            
            # Create products for this category
            for product_data in category_products:
                product = ServiceProduct(**product_data, category_id=category.id)
                db.add(product)
            
            db.commit()
        
        return service
    
    @staticmethod
    def update_service(db: Session, service_id: int, service_data: dict):
        service = ServiceCRUD.get_service(db, service_id)
        if not service:
            return None
        
        for key, value in service_data.items():
            setattr(service, key, value)
        
        db.add(service)
        db.commit()
        db.refresh(service)
        return service
    
    @staticmethod
    def delete_service(db: Session, service_id: int) -> bool:
        """Delete a service and its related categories and products"""
        try:
            # First get the service
            service = db.query(Service).filter(Service.id == service_id).first()
            if not service:
                return False
            
            # Delete all products in this service's categories
            categories = db.query(ServiceCategory).filter(ServiceCategory.service_id == service_id).all()
            for category in categories:
                # Delete all products in this category
                db.query(ServiceProduct).filter(ServiceProduct.category_id == category.id).delete()
            
            # Delete all categories of this service
            db.query(ServiceCategory).filter(ServiceCategory.service_id == service_id).delete()
            
            # Finally delete the service
            db.query(Service).filter(Service.id == service_id).delete()
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error deleting service: {e}")
            return False
    
    @staticmethod
    def get_service_stats(db: Session, service_id: int):
        service = ServiceCRUD.get_service_with_details(db, service_id)
        if not service:
            return {}
        
        categories_count = len(service.categories) if service.categories else 0
        products_count = sum(len(category.products) for category in service.categories) if service.categories else 0
        
        return {
            "categories_count": categories_count,
            "products_count": products_count
        }


class ServiceCategoryCRUD:
    @staticmethod
    def get_categories_by_service(db: Session, service_id: int):
        statement = select(ServiceCategory).where(ServiceCategory.service_id == service_id)
        result = db.execute(statement)
        return result.scalars().all()
    
    @staticmethod
    def get_category(db: Session, category_id: int):
        statement = select(ServiceCategory).where(ServiceCategory.id == category_id)
        result = db.execute(statement)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_category_with_products(db: Session, category_id: int):
        statement = select(ServiceCategory).where(ServiceCategory.id == category_id)
        result = db.execute(statement)
        category = result.scalar_one_or_none()
        
        if category:
            products_stmt = select(ServiceProduct).where(ServiceProduct.category_id == category_id)
            products_result = db.execute(products_stmt)
            category.products = products_result.scalars().all()
        
        return category
    
    @staticmethod
    def create_category(db: Session, service_id: int, category_data: dict):
        category = ServiceCategory(**category_data, service_id=service_id)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def update_category(db: Session, category_id: int, category_data: dict):
        category = ServiceCategoryCRUD.get_category(db, category_id)
        if not category:
            return None
        
        for key, value in category_data.items():
            setattr(category, key, value)
        
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def delete_category(db: Session, category_id: int):
        category = ServiceCategoryCRUD.get_category(db, category_id)
        if not category:
            return False
        
        db.delete(category)
        db.commit()
        return True


class ServiceProductCRUD:
    @staticmethod
    def get_products_by_category(db: Session, category_id: int):
        statement = select(ServiceProduct).where(ServiceProduct.category_id == category_id)
        result = db.execute(statement)
        return result.scalars().all()
    
    @staticmethod
    def get_products_by_service(db: Session, service_id: int, category_id: Optional[int] = None):
        if category_id:
            statement = select(ServiceProduct).join(ServiceCategory).where(
                ServiceCategory.service_id == service_id,
                ServiceProduct.category_id == category_id
            )
        else:
            statement = select(ServiceProduct).join(ServiceCategory).where(
                ServiceCategory.service_id == service_id
            )
        
        result = db.execute(statement)
        return result.scalars().all()
    
    @staticmethod
    def get_all_products(db: Session):
        statement = select(ServiceProduct)
        result = db.execute(statement)
        return result.scalars().all()
    
    @staticmethod
    def get_product(db: Session, product_id: int):
        statement = select(ServiceProduct).where(ServiceProduct.id == product_id)
        result = db.execute(statement)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_product_with_details(db: Session, product_id: int):
        statement = select(ServiceProduct).where(ServiceProduct.id == product_id)
        result = db.execute(statement)
        return result.scalar_one_or_none()
    
    @staticmethod
    def create_product(db: Session, product_data: dict):
        product = ServiceProduct(**product_data)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    
    @staticmethod
    def update_product(db: Session, product_id: int, product_data: dict):
        product = ServiceProductCRUD.get_product(db, product_id)
        if not product:
            return None
        
        for key, value in product_data.items():
            setattr(product, key, value)
        
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    
    @staticmethod
    def update_product_price(db: Session, product_id: int, new_price: float):
        product = ServiceProductCRUD.get_product(db, product_id)
        if not product:
            return None
        
        product.price = new_price
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    
    @staticmethod
    def delete_product(db: Session, product_id: int):
        product = ServiceProductCRUD.get_product(db, product_id)
        if not product:
            return False
        
        db.delete(product)
        db.commit()
        return True