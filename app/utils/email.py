from datetime import datetime, timedelta, timezone
import smtplib
from email.message import EmailMessage
import secrets
import string
import os
from dotenv import load_dotenv

load_dotenv()


def generate_otp(length: int = 6) -> str:
    """Generate numeric OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def otp_expiry(minutes: int = 5):
    """Return OTP expiry time"""
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_email = os.getenv("SMTP_EMAIL")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

        if not self.smtp_email or not self.smtp_password:
            raise ValueError("SMTP credentials not found in environment variables")

        self.from_email = self.smtp_email  

    def send_verification_email(self, to_email: str, otp: str) -> bool:
        """Send OTP email. Returns True if success."""
        try:
            msg = EmailMessage()
            msg.set_content(
                f"""Hello,

Your verification code is: {otp}

This code is valid for 5 minutes. Please do not share this code with anyone.

If you didn't request this code, please ignore this email.

Best regards,
MyBlog Team"""
            )
            msg["Subject"] = "Email Verification - MyBlog"
            msg["From"] = self.from_email
            msg["To"] = to_email

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.smtp_email, self.smtp_password)
            server.send_message(msg)
            server.quit()

            print("✅ EMAIL SENT SUCCESSFULLY to", to_email)
            return True

        except Exception as e:
            print("❌ EMAIL FAILED:", str(e))
            return False