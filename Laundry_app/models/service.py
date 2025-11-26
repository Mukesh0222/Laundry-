# models/service.py
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
    
    categories: List["ServiceCategory"] = Relationship(back_populates="service")

class ServiceCategory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    # description: Optional[str] = None
    description: Optional[str] = None
    service_id: int = Field(foreign_key="service.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
    
    service: Service = Relationship(back_populates="categories")
    products: List["ServiceProduct"] = Relationship(back_populates="category")

class ServiceProduct(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    # description: Optional[str] = None
    price: float = Field(gt=0)
    image_url: Optional[str] = None
    is_active: bool = Field(default=True)
    is_available: bool = Field(default=True)
    category_id: int = Field(foreign_key="servicecategory.id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
    
    category: ServiceCategory = Relationship(back_populates="products")