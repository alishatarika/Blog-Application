from sqlalchemy import Column, Integer, String, DateTime ,Boolean ,Index
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime, timezone
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100))
    email = Column(String(150), unique=True)
    password = Column(String(255))
    status = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    posts = relationship("Post", back_populates="author", lazy="dynamic")
    comments = relationship("Comment", back_populates="user")

    def to_dict(self, include_posts=False, include_comments=False):
        user_dict = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "status": self.status,
            "created_at": self.created_at.strftime("%B %d, %Y %H:%M:%S") if self.created_at else None,
            "deleted_at": self.deleted_at.strftime("%B %d, %Y %H:%M:%S") if self.deleted_at else None,
        }

        if include_posts:
            user_dict["posts"] = [post.to_dict() for post in self.posts.all()] if self.posts else []

        if include_comments:
            user_dict["comments"] = [comment.to_dict() for comment in self.comments] if self.comments else []

        return user_dict