from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.post import Post
from app.models.comments import Comment
from app.utils.hashing import verify_password


def authenticate_user(db: Session, identifier: str, password: str):
    """
    Authenticate user by username or email.
    
    Args:
        db: Database session
        identifier: Username or email
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
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
        raise HTTPException(
            status_code=500, 
            detail="Database error during authentication"
        )

    if not user:
        return None

    try:
        if not verify_password(password, user.password):
            return None
    except Exception as e:
        print("Password verification error:", e)
        raise HTTPException(
            status_code=500, 
            detail="Authentication error"
        )

    return user


def get_user_by_id(db: Session, user_id: int):
    """
    Get user by ID (excluding soft-deleted users).
    
    Args:
        db: Database session
        user_id: User's ID
        
    Returns:
        User object if found, None otherwise
    """
    try:
        return (
            db.query(User)
            .filter(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
            .first()
        )
    except SQLAlchemyError as e:
        print("DB Error fetching user:", e)
        raise HTTPException(
            status_code=500,
            detail="Database error"
        )


def delete_user_account(db: Session, user_id: int):
    """
    Soft-delete user and all their associated data atomically.
    Deletes: user account, all posts, all comments
    
    Args:
        db: Database session
        user_id: User's ID to delete
        
    Returns:
        bool: True if deletion successful
        
    Raises:
        HTTPException: If user not found or database error
    """
    try:
        now = datetime.now(timezone.utc)

        # Soft-delete all user's comments
        db.query(Comment).filter(
            Comment.user_id == user_id,
            Comment.deleted_at.is_(None),
        ).update(
            {"deleted_at": now, "status": False},
            synchronize_session="fetch"
        )

        # Soft-delete all user's posts
        db.query(Post).filter(
            Post.user_id == user_id,
            Post.deleted_at.is_(None),
        ).update(
            {"deleted_at": now, "status": False},
            synchronize_session="fetch"
        )

        # Get and soft-delete user
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None),
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.deleted_at = now
        user.status = False
        
        db.commit()
        return True

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error deleting account:", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to delete account"
        )

    except Exception as e:
        db.rollback()
        print("Unexpected error deleting account:", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to delete account"
        )


def update_user_status(db: Session, user_id: int, status: bool):
    """
    Update user's active status.
    
    Args:
        db: Database session
        user_id: User's ID
        status: New status (True=active, False=inactive)
        
    Returns:
        User: Updated user object
        
    Raises:
        HTTPException: If user not found or database error
    """
    try:
        user = get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.status = status
        db.commit()
        db.refresh(user)
        
        return user
        
    except HTTPException:
        raise
        
    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error updating user status:", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to update user status"
        )