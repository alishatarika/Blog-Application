from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime, timezone
from sqlalchemy.sql import func

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    image_url = Column(String(500), nullable=True)  # NEW: Store image file path
    status = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    comments = relationship(
        "Comment",
        primaryjoin="and_(Comment.post_id==Post.id, Comment.deleted_at==None)",
        back_populates="post",
    )
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "image_url": self.image_url,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_id": self.user_id,
            "author": {"id": self.author.id, "username": self.author.username} if self.author else {"id": self.user_id, "username": "Unknown"},
            "comments": [c.to_dict() for c in self.comments] if self.comments else []
        }
