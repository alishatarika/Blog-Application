from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.post import Post
from app.models.comments import Comment
from app.utils.hashing import verify_password

def authenticate_user(db: Session, identifier: str, password: str):
    try:
        user = (
            db.query(User)
            .filter(
                (User.username == identifier) | (User.email == identifier),
                User.deleted_at.is_(None),       
            )
            .first()
        )
    except SQLAlchemyError as e:
        print("DB Error during authentication:", e)
        raise HTTPException(status_code=500, detail="Database error during authentication")

    if not user:
        return None
    try:
        if not verify_password(password, user.password):
            return None
    except Exception as e:
        print("Password verification error:", e)
        raise HTTPException(status_code=500, detail="Authentication error")

    return user


def delete_user_account(db: Session, user_id: int):
    """
    Soft-deletes the user and every piece of data they own,
    all inside a single transaction so it's atomic.
    """
    try:
        now = datetime.now(timezone.utc)

        db.query(Comment).filter(
            Comment.user_id == user_id,
            Comment.deleted_at.is_(None),
        ).update({"deleted_at": now}, synchronize_session="fetch")

        db.query(Post).filter(
            Post.user_id == user_id,
            Post.deleted_at.is_(None),
        ).update({"deleted_at": now}, synchronize_session="fetch")

        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None),
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.deleted_at = now
        user.status=False
        db.commit()
        return True

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error deleting account:", e)
        raise HTTPException(status_code=500, detail="Failed to delete account")

    except Exception as e:
        db.rollback()
        print("Unexpected error deleting account:", e)
        raise HTTPException(status_code=500, detail="Failed to delete account")