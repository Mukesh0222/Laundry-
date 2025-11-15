from .auth import router as auth_router
from .user import router as user_router
from .address import router as address_router
from .order import router as order_router
from .order_item import router as order_item_router
from .pickups_deliveries import router as pickups_deliveries_router

__all__ = [
    "auth_router",
    "user_router",
    "address_router", 
    "order_router",
    "order_item_router",
    "pickups_deliveries_router"
]