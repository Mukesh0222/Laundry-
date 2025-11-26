# services/otp_service.py
import requests
import random
from datetime import datetime, timedelta

class Bulk9OTPService:
    def __init__(self):
        
        self.api_key = "bk9_your_actual_api_key_here"  
        self.base_url = "https://bulk9.com/api"
        self.sender_id = "LAUNDY"  
    
    def generate_otp(self):
        
        return str(random.randint(100000, 999999))
    
    def send_otp(self, mobile_number, customer_name=""):
        
        try:
            otp = self.generate_otp()
            
            
            message = f"Dear {customer_name}, your LaundryApp OTP is {otp}. Valid for 10 minutes."
            
            
            url = f"{self.base_url}/reseller/sms"
            
            
            payload = {
                "to": mobile_number,
                "message": message,
                "sender": self.sender_id,
                "type": "transactional"  
            }
            
            
            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'success':
                    return {
                        'success': True,
                        'otp': otp,
                        'message_id': result.get('message_id'),
                        'cost': result.get('cost', 0),
                        'message': 'OTP sent successfully'
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('message', 'Failed to send OTP')
                    }
            else:
                return {
                    'success': False,
                    'error': f'API Error: {response.status_code}',
                    'message': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_balance(self):
        
        url = f"{self.base_url}/reseller/balance"
        headers = {"Authorization": self.api_key}
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def get_otp_service():
    return Bulk9OTPService()