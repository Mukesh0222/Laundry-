# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlmodel import Session
# from typing import Dict, Any

# from db.session import get_db
# from services.dashboard_service import DashboardService
# from schemas.dashboard import DashboardResponse
# from dependencies.auth import get_current_user, get_current_staff_user
# from models.user import User

# router = APIRouter()

# @router.get("/", response_model=DashboardResponse)
# def get_dashboard(
#     period_days: int = Query(30, description="Period for analytics in days"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)  # Only staff/admin can access dashboard
# ):
#     """
#     Get complete dashboard data
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_complete_dashboard(period_days)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")

# @router.get("/stats")
# def get_dashboard_stats(
#     period_days: int = Query(30, description="Period for analytics in days"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get only statistics data
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_dashboard_stats(period_days)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

# @router.get("/revenue-chart")
# def get_revenue_chart(
#     days: int = Query(30, description="Number of days for chart"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get revenue chart data
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_revenue_chart_data(days)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching revenue chart: {str(e)}")

# @router.get("/service-distribution")
# def get_service_distribution(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get service type distribution
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_service_distribution()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching service distribution: {str(e)}")

# @router.get("/category-stats")
# def get_category_stats(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get category-wise statistics
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_category_stats()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching category stats: {str(e)}")

# @router.get("/recent-orders")
# def get_recent_orders(
#     limit: int = Query(10, description="Number of recent orders to fetch"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get recent orders
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_recent_orders(limit)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching recent orders: {str(e)}")

# @router.get("/top-customers")
# def get_top_customers(
#     limit: int = Query(5, description="Number of top customers to fetch"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get top customers
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_top_customers(limit)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching top customers: {str(e)}")

# @router.get("/quick-stats")
# def get_quick_stats(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get quick stats for dashboard cards
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_quick_stats()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching quick stats: {str(e)}")


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import Dict, Any

from db.session import get_db
from services.dashboard_service import DashboardService
from schemas.dashboard import DashboardResponse
from dependencies.auth import get_current_user, get_current_staff_user
from models.user import User
from models.order import Order  
from models.order_item import OrderItem 

router = APIRouter()

@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    period_days: int = Query(30, description="Period for analytics in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)  
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

# @router.get("/revenue-chart")
# def get_revenue_chart(
#     days: int = Query(30, description="Number of days for chart"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get revenue chart data
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_revenue_chart_data(days)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching revenue chart: {str(e)}")

# @router.get("/service-distribution")
# def get_service_distribution(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get service type distribution
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_service_distribution()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching service distribution: {str(e)}")

# @router.get("/category-stats")
# def get_category_stats(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get category-wise statistics
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_category_stats()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching category stats: {str(e)}")

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
        print(f"Fetching recent orders. Limit: {limit}")
        
        # Direct implementation without service class to avoid errors
        recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(limit).all()
        
        print(f"Found {len(recent_orders)} orders")
        
        orders_response = []
        for order in recent_orders:
            try:
                # Get user details
                user = db.get(User, order.user_id)
                
                # Get order items count and total quantity
                order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
                total_items = len(order_items)
                total_quantity = sum(item.quantity for item in order_items)
                
                order_data = {
                    "order_id": order.order_id,
                    "Token_no": order.Token_no,
                    "customer_name": user.name if user else "Unknown",
                    "customer_mobile": user.mobile_no if user else "Unknown",
                    "service": order.service,
                    "status": order.status,
                    "total_items": total_items,
                    "total_quantity": total_quantity,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "user_id": order.user_id
                }
                
                orders_response.append(order_data)
                
            except Exception as order_error:
                print(f"Error processing order {order.order_id}: {str(order_error)}")
                continue
        
        return {
            "success": True,
            "recent_orders": orders_response,
            "total_count": len(orders_response)
        }
        
    except Exception as e:
        print(f"Recent orders error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching recent orders: {str(e)}")
    
# @router.get("/top-customers")
# def get_top_customers(
#     limit: int = Query(5, description="Number of top customers to fetch"),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get top customers
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_top_customers(limit)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching top customers: {str(e)}")

# @router.get("/quick-stats")
# def get_quick_stats(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_staff_user)
# ):
#     """
#     Get quick stats for dashboard cards
#     """
#     try:
#         dashboard_service = DashboardService(db)
#         return dashboard_service.get_quick_stats()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching quick stats: {str(e)}")