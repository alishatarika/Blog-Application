from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.otp import OTP
from app.utils.email import generate_otp, otp_expiry, EmailService


def create_and_send_otp(db: Session, email: str) -> bool:
    try:
        db.query(OTP).filter(OTP.email == email).delete()
        db.commit()

        otp_code = generate_otp(6)
        expires_at = otp_expiry(5)
        new_otp = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            is_verified=False
        )
        db.add(new_otp)
        db.commit()

        email_service = EmailService()
        email_sent = email_service.send_verification_email(email, otp_code)

        if not email_sent:
            db.delete(new_otp)
            db.commit()
            return False

        return True

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error creating OTP:", e)
        return False

    except Exception as e:
        db.rollback()
        print("Error creating OTP:", e)
        return False


def verify_otp(db: Session, email: str, otp_code: str) -> bool:
    try:
        otp_record = (
            db.query(OTP)
            .filter(
                OTP.email == email,
                OTP.otp_code == otp_code,
                OTP.is_verified == False
            )
            .order_by(OTP.created_at.desc())
            .first()
        )

        if not otp_record:
            print(f"No OTP record found for email: {email}, code: {otp_code}")
            return False

        now = datetime.now(timezone.utc)
        
        expires_at = otp_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        print(f"Current time: {now}, Expires at: {expires_at}")
        
        if now > expires_at:
            print("OTP has expired")
            return False
        otp_record.is_verified = True
        db.commit()
        print("OTP verified successfully")
        return True

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error verifying OTP:", e)
        return False

    except Exception as e:
        db.rollback()
        print("Error verifying OTP:", e)
        import traceback
        traceback.print_exc()
        return False


def is_email_verified(db: Session, email: str) -> bool:
    try:
        verified_otp = (
            db.query(OTP)
            .filter(
                OTP.email == email,
                OTP.is_verified == True
            )
            .order_by(OTP.created_at.desc())
            .first()
        )

        if not verified_otp:
            return False

        now = datetime.now(timezone.utc)
        
        created_at = verified_otp.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        time_diff = (now - created_at).total_seconds() / 60

        return time_diff <= 30

    except Exception as e:
        print("Error checking email verification:", e)
        import traceback
        traceback.print_exc()
        return False


def cleanup_expired_otps(db: Session):
    """
    Delete expired OTP records (cleanup job).
    """
    try:
        now = datetime.now(timezone.utc)
        expired_otps = db.query(OTP).all()
        
        for otp in expired_otps:
            expires_at = otp.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < now:
                db.delete(otp)
        
        db.commit()
        print("Cleaned up expired OTPs")
        
    except Exception as e:
        db.rollback()
        print("Error cleaning up OTPs:", e)
        import traceback
        traceback.print_exc()