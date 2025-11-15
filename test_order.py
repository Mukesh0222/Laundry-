# import requests
# import json

# def working_order_creation():
#     url = "http://192.168.1.8:8000/api/v1/orders/"
    
#     # 1. Get fresh token from login
#     mobile_no = "3338226509"
    
#     # Login and get token
#     login_response = requests.post(
#         "http://192.168.1.8:8000/api/v1/login",
#         json={"mobile_no": mobile_no}
#     )
    
#     if login_response.status_code != 200:
#         print("Login failed")
#         return
    
#     # Get OTP and verify
#     otp = input("Enter OTP: ")
#     verify_response = requests.post(
#         "http://192.168.1.8:8000/api/v1/verify-otp",
#         json={"mobile_no": mobile_no, "otp": otp}
#     )
    
#     if verify_response.status_code != 200:
#         print("OTP verification failed")
#         return
    
#     token_data = verify_response.json()
#     access_token = token_data["access_token"]
    
#     # 2. Create order with token in HEADER
#     headers = {
#         "Authorization": f"Bearer {access_token}",  #  HEADER
#         "Content-Type": "application/json"
#     }
    
#     order_data = {
#         "address_id": 2,                          #  BODY
#         "service": "wash_iron",
#         "items": [
#             {
#                 "category_name": "kids",
#                 "product_name": "t-shirts",
#                 "quantity": 3
#             }
#         ]
#     }
    
#     response = requests.post(url, headers=headers, json=order_data)
#     print(f"Status: {response.status_code}")
#     print(f"Response: {response.text}")

# if __name__ == "__main__":
#     working_order_creation()

