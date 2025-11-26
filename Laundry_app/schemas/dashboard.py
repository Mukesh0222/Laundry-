from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, date
from decimal import Decimal

class DashboardStats(BaseModel):
    total_orders: int
    total_revenue: float
    pending_orders: int
    completed_orders: int
    total_customers: int
    monthly_revenue: float
    weekly_revenue: float
    
    
    revenue_growth: float = 0.0
    order_growth: float = 0.0
    customer_growth: float = 0.0

    class Config:
        arbitrary_types_allowed = True

class RevenueChartData(BaseModel):
    labels: List[str]  
    revenue: List[float]
    orders: List[int]

    class Config:
        arbitrary_types_allowed = True

class ServiceDistribution(BaseModel):
    service_type: str
    count: int
    percentage: float
    revenue: float

class CategoryWiseStats(BaseModel):
    category_name: str
    total_items: int
    total_revenue: float
    percentage: float

class RecentOrder(BaseModel):
    order_id: int
    token_no: str
    customer_name: str
    service_type: str
    status: str
    total_amount: float
    created_at: datetime
    item_count: int

class TopCustomer(BaseModel):
    user_id: int
    customer_name: str
    total_orders: int
    total_spent: float
    last_order_date: datetime

class QuickStats(BaseModel):
    today_orders: int
    today_revenue: float
    week_revenue: float
    avg_order_value: float
    total_services: int

class DashboardResponse(BaseModel):
    stats: DashboardStats
    revenue_chart: RevenueChartData
    service_distribution: List[ServiceDistribution]
    category_stats: List[CategoryWiseStats]
    recent_orders: List[RecentOrder]
    top_customers: List[TopCustomer]
    quick_stats: QuickStats

    class Config:
        arbitrary_types_allowed = True
        