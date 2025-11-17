# api/otp.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

# Import the OTP service
from services.otp_service import Bulk9OTPService

router = APIRouter(prefix="/api/otp", tags=["OTP"])

# OTP Request Schema
class OTPRequest(BaseModel):
    mobile_number: str
    customer_name: Optional[str] = ""

class OTPVerify(BaseModel):
    mobile_number: str
    otp: str

# Create OTP service instance
otp_service = Bulk9OTPService()

@router.post("/send")
async def send_otp(request: OTPRequest):
    """
    Laundry customer-க்கு OTP அனுப்ப
    """
    result = otp_service.send_otp(
        mobile_number=request.mobile_number,
        customer_name=request.customer_name
    )
    
    if not result['success']:
        raise HTTPException(
            status_code=400, 
            detail=result['error']
        )
    
    return {
        "success": True,
        "message": "OTP sent successfully",
        "mobile": request.mobile_number,
        "validity": "10 minutes"
    }

@router.post("/verify")
async def verify_otp(request: OTPVerify):
    """
    OTP verify செய்ய (இப்போது simple-ஆக)
    """
    # TODO: Database-ல் OTP store & verify செய்ய
    return {
        "success": True,
        "message": "OTP verification implemented soon",
        "mobile": request.mobile_number
    }

@router.get("/balance")
async def get_balance():
    """Bulk9 account balance-ஐ பார்க்க"""
    balance = otp_service.check_balance()
    return balance