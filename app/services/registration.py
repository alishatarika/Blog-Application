from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.registration import RegisterSchema
from app.utils.hashing import hash_password

def register_user_service(db: Session, user_data: RegisterSchema):
    try:
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already registered")
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password=hash_password(user_data.password),
            status=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error during registration:", e)
        raise HTTPException(status_code=500, detail="Database error during registration")

    except Exception as e:
        db.rollback()
        print("Unexpected error during registration:", e)
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")