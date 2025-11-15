from typing import Optional
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import os

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
    
    def send_otp_email(self, recipient_email: str, otp: str, user_name: str) -> bool:
        try:
            message = MimeMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = "Your OTP Code - Laundry App"
            
            body = f"""
            Hello {user_name},
            
            Your OTP code for verification is: {otp}
            
            This OTP will expire in 10 minutes.
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            Laundry App Team
            """
            
            message.attach(MimeText(body, "plain"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_password_reset_email(self, recipient_email: str, reset_token: str, user_name: str) -> bool:
        # Implementation for password reset email
        # Similar to send_otp_email but with different content
        return True

email_service = EmailService()