import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from db.session import create_db_and_tables
from core.config import settings
from api.auth import router as auth_router
# from api.staff_auth import router as staff_auth_router
from api.user import router as user_router
from api.address import router as address_router
from api.order import router as order_router
from api.order_item import router as order_item_router
from api.dashboard import router as dashboard_router
from api.pickups_deliveries import router as pickups_deliveries_router
from api.admin import router as admin_router
from api.customers import router as customers_router
from api.staff_management import router as staff_management_router
from fastapi.middleware.cors import CORSMiddleware
from api.staff import router as staff_router
from dependencies.auth import get_current_user
from api.otp import router as otp_router
from api.pricing import router as pricing_router 
from api.order_archive import router as order_archive_router
from api.service import router as service_router
from api.feedback import router as feedback_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    create_db_and_tables()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8081", "http://192.168.1.3:8081", "http://localhost:5174", "http://192.168.1.8:5173", "http://192.168.1.16:5174",
    "http://localhost:5175", "http://192.168.1.16:5175", "http://192.168.1.6:5173", "http://localhost:5173" ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # allow_origins = [
    #     '/^http:\/\/localhost(:[0-9]+)?$/',
    #     '/^http:\/\/127\.0\.0\.1(:[0-9]+)?$/',
    #     '/^http:\/\/10\.\d+\.\d+\.\d+(:[0-9]+)?$/',
    #     '/^http:\/\/192\.168\.\d+\.\d+(:[0-9]+)?$/',
    #     '/^exp:\/\/10\.\d+\.\d+\.\d+(:[0-9]+)?$/',
    # ],
    )


# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR, tags=["auth"])
# app.include_router(staff_auth_router, prefix="/api/v1/staff/auth", tags=["staff-auth"])
app.include_router(user_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(address_router, prefix=f"{settings.API_V1_STR}/addresses", tags=["addresses"])
app.include_router(order_router, prefix=f"{settings.API_V1_STR}/orders", tags=["orders"])
app.include_router(order_item_router, prefix=f"{settings.API_V1_STR}/order-items", tags=["order-items"])
app.include_router(pickups_deliveries_router, prefix=f"{settings.API_V1_STR}/pickups-deliveries", tags=["pickups-deliveries"])
app.include_router(staff_router, prefix="/api/v1/staff/orders", tags=["staff"])
app.include_router(order_router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
app.include_router(staff_management_router, prefix="/api/v1/staff", tags=["Staff Management"])
# app.include_router(otp_router)
app.include_router(dashboard_router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Dashboard"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(customers_router, prefix="/api/v1/customers", tags=["customers"])
app.include_router(service_router, prefix="/api/v1", tags=["services"])
app.include_router(pricing_router, prefix=f"{settings.API_V1_STR}/pricing", tags=["pricing"])
app.include_router(order_archive_router, prefix=f"{settings.API_V1_STR}", tags=["order-archive"])
app.include_router(feedback_router, prefix="/api/v1", tags=["feedback"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Laundry project API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("=== VALIDATION ERROR DETAILS ===")
    print(f"URL: {request.url}")
    print(f"Method: {request.method}")
    print(f"Headers: {request.headers}")
    print(f"Validation errors: {exc.errors()}")
    print("=== END VALIDATION ERROR ===")
    
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)