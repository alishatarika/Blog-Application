from fastapi import Cookie, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from app.models.user import User
from app.database.connection import get_db
from app.utils.jwt_handler import decode_token
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False 
)

# ---------------- TOKEN EXTRACTOR ----------------
def get_token(
    access_token: str = Cookie(None),
    bearer_token: str = Depends(oauth2_scheme),
):
    return access_token or bearer_token

# ---------------- REQUIRED LOGIN ----------------
def get_current_user(
    response: Response,
    token: str = Depends(get_token),
    db: Session = Depends(get_db),
):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(token)
    if not payload:
        response.delete_cookie("access_token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(
        User.id == payload.get("user_id"),
        User.deleted_at.is_(None)
    ).first()

    if not user:
        response.delete_cookie("access_token")
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ---------------- OPTIONAL LOGIN ----------------
def get_current_user_optional(
    token: str = Depends(get_token),
    db: Session = Depends(get_db),
):
    if not token:
        return None

    payload = decode_token(token)
    if not payload:
        return None

    return db.query(User).filter(
        User.id == payload.get("user_id"),
        User.deleted_at.is_(None)
    ).first()
