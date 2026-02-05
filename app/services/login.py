from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.utils.hashing import verify_password

def login_user_service(db: Session, identifier: str, password: str):
    try:
        user = (
            db.query(User)
            .filter(
                or_(User.username == identifier, User.email == identifier),
                User.deleted_at.is_(None),       
            )
            .first()
        )
    except SQLAlchemyError as e:
        print("DB Error during user lookup:", e)
        raise HTTPException(status_code=500, detail="Database error during login")

    if not user:
        return None  

    try:
        if not verify_password(password, user.password):
            return None  
    except Exception as e:
        print("Password verification error:", e)
        raise HTTPException(status_code=500, detail="Authentication error")

    return user