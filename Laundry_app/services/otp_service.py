# services/otp_service.py
import requests
import random
from datetime import datetime, timedelta

class Bulk9OTPService:
    def __init__(self):
        # 🔑 உங்கள் Actual Bulk9 API Key-ஐ இங்கு Add செய்யவும்
        self.api_key = "bk9_your_actual_api_key_here"  # ⚠️ Replace with real key
        self.base_url = "https://bulk9.com/api"
        self.sender_id = "LAUNDY"  # உங்கள் registered sender ID
    
    def generate_otp(self):
        """6 digit OTP generate செய்ய"""
        return str(random.randint(100000, 999999))
    
    def send_otp(self, mobile_number, customer_name=""):
        """
        Laundry customer-க்கு OTP அனுப்ப
        """
        try:
            otp = self.generate_otp()
            
            # OTP message template
            message = f"Dear {customer_name}, your LaundryApp OTP is {otp}. Valid for 10 minutes."
            
            # API endpoint
            url = f"{self.base_url}/reseller/sms"
            
            # Request payload
            payload = {
                "to": mobile_number,
                "message": message,
                "sender": self.sender_id,
                "type": "transactional"  # OTP SMS
            }
            
            # Headers with API Key
            headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            
            # POST request send செய்ய
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
        """Bulk9-ல் balance check செய்ய"""
        url = f"{self.base_url}/reseller/balance"
        headers = {"Authorization": self.api_key}
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

# Usage in other files
def get_otp_service():
    return Bulk9OTPService()