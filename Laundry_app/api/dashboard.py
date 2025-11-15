from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import Dict, Any

from db.session import get_db
from services.dashboard_service import DashboardService
from schemas.dashboard import DashboardResponse
from dependencies.auth import get_current_user, get_current_staff_user
from models.user import User

router = APIRouter()

@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    period_days: int = Query(30, description="Period for analytics in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)  # Only staff/admin can access dashboard
):
    """
    Get complete dashboard data
    """
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_complete_dashboard(period_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")

@router.get("/stats")
def get_dashboard_stats(
    period_days: int = Query(30, description="Period for analytics in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """
    Get only statistics data
    """
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_dashboard_stats(period_days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@router.get("/revenue-chart")
def get_revenue_chart(
    days: int = Query(30, description="Number of days for chart"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """
    Get revenue chart data
    """
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_revenue_chart_data(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching revenue chart: {str(e)}")

@router.get("/service-distribution")
def get_service_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """
    Get service type distribution
    """
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_service_distribution()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching service distribution: {str(e)}")

@router.get("/category-stats")
def get_category_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """
    Get category-wise statistics
    """
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_category_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category stats: {str(e)}")

@router.get("/recent-orders")
def get_recent_orders(
    limit: int = Query(10, description="Number of recent orders to fetch"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """
    Get recent orders
    """
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_recent_orders(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent orders: {str(e)}")

@router.get("/top-customers")
def get_top_customers(
    limit: int = Query(5, description="Number of top customers to fetch"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """
    Get top customers
    """
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_top_customers(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top customers: {str(e)}")

@router.get("/quick-stats")
def get_quick_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """
    Get quick stats for dashboard cards
    """
    try:
        dashboard_service = DashboardService(db)
        return dashboard_service.get_quick_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quick stats: {str(e)}")