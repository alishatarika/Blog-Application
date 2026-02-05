from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime ,Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime, timezone

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    post = relationship("Post", back_populates="comments")
    user = relationship("User")  

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "comment_text": self.comment_text,
            "created_at": self.created_at,
            "user": {"id": self.user.id, "username": self.user.username} if self.user else None
        }

    