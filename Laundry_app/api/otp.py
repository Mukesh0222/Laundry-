from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional


from services.otp_service import Bulk9OTPService

router = APIRouter(prefix="/api/otp", tags=["OTP"])


class OTPRequest(BaseModel):
    mobile_number: str
    customer_name: Optional[str] = ""

class OTPVerify(BaseModel):
    mobile_number: str
    otp: str


otp_service = Bulk9OTPService()

@router.post("/send")
async def send_otp(request: OTPRequest):

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
   
    return {
        "success": True,
        "message": "OTP verification implemented soon",
        "mobile": request.mobile_number
    }

@router.get("/balance")
async def get_balance():
    balance = otp_service.check_balance()
    return balance