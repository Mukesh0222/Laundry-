# import requests
# import json

# def debug_order_creation():
#     print(" DEBUG ORDER CREATION - STEP BY STEP")
#     print("=" * 60)
    
#     base_url = "http://192.168.1.8:8000/api/v1"
#     mobile_no = "3338226509"
    
#     # Step 1: Test Server Connection
#     print("1.  Testing Server Connection...")
#     try:
#         test_response = requests.get(f"{base_url}/orders/services/available", timeout=5)
#         print(f"    Server is running - Status: {test_response.status_code}")
#     except Exception as e:
#         print(f"    Server connection failed: {e}")
#         return
    
#     # Step 2: Login
#     print("2.  Requesting OTP...")
#     login_response = requests.post(
#         f"{base_url}/login",
#         json={"mobile_no": mobile_no}
#     )
    
#     print(f"   Login Status: {login_response.status_code}")
#     print(f"   Login Response: {login_response.text}")
    
#     if login_response.status_code != 200:
#         print("    Login failed")
#         return
    
#     # Step 3: OTP Verification
#     otp = input("3.  Enter OTP received on mobile: ")
    
#     print("4.  Verifying OTP...")
#     verify_response = requests.post(
#         f"{base_url}/verify-otp",
#         json={"mobile_no": mobile_no, "otp": otp}
#     )
    
#     print(f"   Verify Status: {verify_response.status_code}")
#     print(f"   Verify Response: {verify_response.text}")
    
#     if verify_response.status_code != 200:
#         print("    OTP verification failed")
#         return
    
#     token_data = verify_response.json()
#     access_token = token_data.get("access_token")
    
#     if not access_token:
#         print("    No access_token in response")
#         return
        
#     print(f"    Access Token: {access_token[:50]}...")
    
#     # Step 4: Create Order with Detailed Debug
#     print("5.  Creating Order with Token in Header...")
    
#     url = f"{base_url}/orders/"
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json",
#         "X-Debug-Info": "Python-Test-Client"
#     }
    
#     order_data = {
#         "address_id": 0,  # Use 0 for default address
#         "service": "wash_iron",
#         "items": [
#             {
#                 "category_name": "kids",
#                 "product_name": "t-shirts",
#                 "quantity": 3
#             }
#         ]
#     }
    
#     print(f"    REQUEST DETAILS:")
#     print(f"      URL: {url}")
#     print(f"      Headers: {json.dumps(headers, indent=6)}")
#     print(f"      Body: {json.dumps(order_data, indent=6)}")
    
#     try:
#         response = requests.post(url, headers=headers, json=order_data, timeout=10)
        
#         print(f"\n6.  RESPONSE DETAILS:")
#         print(f"   Status Code: {response.status_code}")
#         print(f"   Response Headers: {dict(response.headers)}")
#         print(f"   Response Body: {response.text}")
        
#         # Analyze response
#         if response.status_code == 200:
#             order_info = response.json()
#             print("\n ORDER CREATED SUCCESSFULLY!")
#             print(f"   Order ID: {order_info.get('order_id')}")
#             print(f"   Order Number: {order_info.get('order_number')}")
#             print(f"   Status: {order_info.get('status')}")
#         elif response.status_code == 403:
#             print("\n 403 FORBIDDEN - Token authentication failed")
#             print("   Possible reasons:")
#             print("   - Token expired")
#             print("   - Invalid token format")
#             print("   - User not found")
#         elif response.status_code == 401:
#             print("\n 401 UNAUTHORIZED - Authentication required")
#         elif response.status_code == 422:
#             print("\n 422 VALIDATION ERROR - Check request data")
#         else:
#             print(f"\n UNEXPECTED ERROR: {response.status_code}")
            
#     except requests.exceptions.ConnectionError:
#         print("\n CONNECTION ERROR - Cannot reach server")
#     except requests.exceptions.Timeout:
#         print("\n TIMEOUT - Server not responding")
#     except Exception as e:
#         print(f"\n UNEXPECTED ERROR: {e}")

# if __name__ == "__main__":
#     debug_order_creation()
    