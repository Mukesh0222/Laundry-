from sqlmodel import Session, select, func, and_, or_
from typing import List, Tuple, Any, Dict
from datetime import datetime, timedelta, date
from decimal import Decimal
from models.order import Order, OrderStatus, ServiceType
from models.order_item import OrderItem, CategoryName
from models.user import User
from schemas.dashboard import (
    DashboardStats, RevenueChartData, ServiceDistribution, 
    CategoryWiseStats, RecentOrder, TopCustomer, DashboardResponse, QuickStats
)

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_complete_dashboard(self, period_days: int = 30) -> Dict[str, Any]:
        """Get complete dashboard data"""
        try:
            stats = self.get_dashboard_stats(period_days)
            recent_orders = self.get_recent_orders(10)
            service_distribution = self.get_service_distribution()
            
            return {
                "stats": stats,
                "recent_orders": recent_orders,
                "service_distribution": service_distribution,
                "period_days": period_days,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Dashboard service error: {e}")
            raise

    def get_dashboard_stats(self, period_days: int = 30) -> DashboardStats:
        """Get main dashboard statistics"""
        
        # Total orders
        total_orders = self.db.exec(select(func.count(Order.order_id))).first() or 0
        
        # Total revenue
        total_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).select_from(OrderItem)
        total_revenue = self.db.exec(total_revenue_stmt).first() or 0.0
        
        # Pending orders
        pending_orders = self.db.exec(
            select(func.count(Order.order_id)).where(Order.status == OrderStatus.PENDING)
        ).first() or 0
        
        # Completed orders
        completed_orders = self.db.exec(
            select(func.count(Order.order_id)).where(Order.status == OrderStatus.COMPLETED)
        ).first() or 0
        
        # Total customers
        total_customers = self.db.exec(select(func.count(User.user_id))).first() or 0
        
        # Monthly revenue (current month)
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).select_from(OrderItem).join(Order).where(Order.created_at >= current_month_start)
        monthly_revenue = self.db.exec(monthly_revenue_stmt).first() or 0.0
        
        # Weekly revenue (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        weekly_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).select_from(OrderItem).join(Order).where(Order.created_at >= week_ago)
        weekly_revenue = self.db.exec(weekly_revenue_stmt).first() or 0.0
        
        # Calculate growth percentages (compared to previous period)
        prev_period_start = datetime.now() - timedelta(days=period_days * 2)
        prev_period_end = datetime.now() - timedelta(days=period_days)
        
        # Previous period revenue
        prev_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).select_from(OrderItem).join(Order).where(
            and_(
                Order.created_at >= prev_period_start,
                Order.created_at < prev_period_end
            )
        )
        prev_revenue = self.db.exec(prev_revenue_stmt).first() or 0.0
        
        # Previous period orders
        prev_orders_stmt = select(func.count(Order.order_id)).where(
            and_(
                Order.created_at >= prev_period_start,
                Order.created_at < prev_period_end
            )
        )
        prev_orders = self.db.exec(prev_orders_stmt).first() or 0
        
        # Calculate growth percentages
        revenue_growth = self._calculate_growth(total_revenue, prev_revenue)
        order_growth = self._calculate_growth(total_orders, prev_orders)
        
        return DashboardStats(
            total_orders=total_orders,
            total_revenue=float(total_revenue),
            pending_orders=pending_orders,
            completed_orders=completed_orders,
            total_customers=total_customers,
            monthly_revenue=float(monthly_revenue),
            weekly_revenue=float(weekly_revenue),
            revenue_growth=revenue_growth,
            order_growth=order_growth,
            customer_growth=0.0
        )

    def get_revenue_chart_data(self, days: int = 30) -> RevenueChartData:
        """Get revenue chart data for the specified number of days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate all dates in the range
        date_labels = []
        revenue_data = []
        orders_data = []
        
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_labels.append(current_date.strftime("%Y-%m-%d"))
            
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())
            
            # Daily revenue
            daily_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).select_from(OrderItem).join(Order).where(
                and_(
                    Order.created_at >= day_start,
                    Order.created_at <= day_end
                )
            )
            daily_revenue = self.db.exec(daily_revenue_stmt).first() or 0.0
            revenue_data.append(float(daily_revenue))
            
            # Daily orders
            daily_orders_stmt = select(func.count(Order.order_id)).where(
                and_(
                    Order.created_at >= day_start,
                    Order.created_at <= day_end
                )
            )
            daily_orders = self.db.exec(daily_orders_stmt).first() or 0
            orders_data.append(daily_orders)
            
            current_date += timedelta(days=1)
        
        return RevenueChartData(
            labels=date_labels,
            revenue=revenue_data,
            orders=orders_data
        )

    def get_service_distribution(self) -> List[ServiceDistribution]:
        """Get service type distribution"""
        total_orders_stmt = select(func.count(Order.order_id))
        total_orders = self.db.exec(total_orders_stmt).first() or 1
        
        service_stats = []
        for service_type in ServiceType:
            # Count orders by service type
            service_count_stmt = select(func.count(Order.order_id)).where(Order.service == service_type)
            service_count = self.db.exec(service_count_stmt).first() or 0
            
            # Revenue by service type
            service_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).select_from(OrderItem).join(Order).where(Order.service == service_type)
            service_revenue = self.db.exec(service_revenue_stmt).first() or 0.0
            
            percentage = (service_count / total_orders) * 100 if total_orders > 0 else 0
            
            service_stats.append(ServiceDistribution(
                service_type=service_type.value,
                count=service_count,
                percentage=round(percentage, 2),
                revenue=float(service_revenue)
            ))
        
        return service_stats

    def get_category_stats(self) -> List[CategoryWiseStats]:
        """Get category-wise statistics"""
        # Total items across all categories
        total_items_stmt = select(func.sum(OrderItem.quantity))
        total_items = self.db.exec(total_items_stmt).first() or 1
        
        category_stats = []
        for category in CategoryName:
            # Items count by category
            category_count_stmt = select(func.coalesce(func.sum(OrderItem.quantity), 0)).where(OrderItem.category_name == category)
            category_count = self.db.exec(category_count_stmt).first() or 0
            
            # Revenue by category
            category_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).where(OrderItem.category_name == category)
            category_revenue = self.db.exec(category_revenue_stmt).first() or 0.0
            
            percentage = (category_count / total_items) * 100 if total_items > 0 else 0
            
            category_stats.append(CategoryWiseStats(
                category_name=category.value,
                total_items=category_count,
                total_revenue=float(category_revenue),
                percentage=round(percentage, 2)
            ))
        
        # Filter out categories with zero items
        return [stat for stat in category_stats if stat.total_items > 0]

    def get_recent_orders(self, limit: int = 10) -> List[RecentOrder]:
        """Get recent orders with customer details"""
        stmt = (
            select(Order, User)
            .join(User, Order.user_id == User.user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        
        results = self.db.exec(stmt).all()
        recent_orders = []
        
        for order, user in results:
            # Get item count for this order
            item_count_stmt = select(func.sum(OrderItem.quantity)).where(OrderItem.order_id == order.order_id)
            item_count = self.db.exec(item_count_stmt).first() or 0
            
            # Get total amount for this order
            order_amount_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).where(OrderItem.order_id == order.order_id)
            order_amount = self.db.exec(order_amount_stmt).first() or 0.0
            
            recent_orders.append(RecentOrder(
                order_id=order.order_id,
                token_no=order.Token_no,
                customer_name=user.name,
                service_type=order.service.value,
                status=order.status.value,
                total_amount=float(order_amount),
                created_at=order.created_at,
                item_count=item_count
            ))
        
        return recent_orders

    def get_top_customers(self, limit: int = 5) -> List[TopCustomer]:
        """Get top customers by order count and spending"""
        stmt = (
            select(
                User.user_id,
                User.name,
                func.count(Order.order_id).label('total_orders'),
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label('total_spent'),
                func.max(Order.created_at).label('last_order_date')
            )
            .select_from(User)
            .join(Order, User.user_id == Order.user_id)
            .join(OrderItem, Order.order_id == OrderItem.order_id)
            .group_by(User.user_id, User.name)
            .having(func.count(Order.order_id) > 0)
            .order_by(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).desc())
            .limit(limit)
        )
        
        results = self.db.exec(stmt).all()
        top_customers = []
        
        for row in results:
            top_customers.append(TopCustomer(
                user_id=row.user_id,
                customer_name=row.name,
                total_orders=row.total_orders,
                total_spent=float(row.total_spent),
                last_order_date=row.last_order_date
            ))
        
        return top_customers

    def get_quick_stats(self) -> QuickStats:
        """Get quick stats for dashboard cards"""
        # Today's stats
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Today's orders
        today_orders_stmt = select(func.count(Order.order_id)).where(
            and_(
                Order.created_at >= today_start,
                Order.created_at <= today_end
            )
        )
        today_orders = self.db.exec(today_orders_stmt).first() or 0
        
        # Today's revenue
        today_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).select_from(OrderItem).join(Order).where(
            and_(
                Order.created_at >= today_start,
                Order.created_at <= today_end
            )
        )
        today_revenue = self.db.exec(today_revenue_stmt).first() or 0.0
        
        # This week's revenue
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).select_from(OrderItem).join(Order).where(
            Order.created_at >= week_start
        )
        week_revenue = self.db.exec(week_revenue_stmt).first() or 0.0
        
        # Average order value
        total_orders_stmt = select(func.count(Order.order_id))
        total_orders = self.db.exec(total_orders_stmt).first() or 1
        total_revenue_stmt = select(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0))
        total_revenue = self.db.exec(total_revenue_stmt).first() or 0.0
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return QuickStats(
            today_orders=today_orders,
            today_revenue=float(today_revenue),
            week_revenue=float(week_revenue),
            avg_order_value=float(avg_order_value),
            total_services=len(ServiceType)
        )

    def _calculate_growth(self, current: float, previous: float) -> float:
        """Calculate growth percentage"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    def get_complete_dashboard(self, period_days: int = 30) -> DashboardResponse:
        """Get complete dashboard data"""
        return DashboardResponse(
            stats=self.get_dashboard_stats(period_days),
            revenue_chart=self.get_revenue_chart_data(period_days),
            service_distribution=self.get_service_distribution(),
            category_stats=self.get_category_stats(),
            recent_orders=self.get_recent_orders(),
            top_customers=self.get_top_customers(),
            quick_stats=self.get_quick_stats()
        )