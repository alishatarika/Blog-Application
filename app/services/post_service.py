from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.post import Post
from app.models.comments import Comment
from app.schemas.post import PostCreate, PostUpdate
from app.schemas.comment import CommentCreate

def create_post(db: Session, post: PostCreate, user_id: int):
    try:
        new_post = Post(
            title=post.title,
            content=post.content,
            image_url=post.image_url,
            user_id=user_id,
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error creating post:", e)
        raise HTTPException(status_code=500, detail="Failed to create post")

    except Exception as e:
        db.rollback()
        print("Unexpected error creating post:", e)
        raise HTTPException(status_code=500, detail="Failed to create post")


def get_all_posts(db: Session):
    try:
        return (
            db.query(Post)
            .filter(Post.deleted_at.is_(None))
            .order_by(Post.created_at.desc())
            .all()
        )
    except SQLAlchemyError as e:
        print("DB Error fetching posts:", e)
        raise HTTPException(status_code=500, detail="Failed to fetch posts")


def get_post_by_id(db: Session, post_id: int):
    try:
        return (
            db.query(Post)
            .filter(Post.id == post_id, Post.deleted_at.is_(None))
            .first()
        )
    except SQLAlchemyError as e:
        print("DB Error fetching post:", e)
        raise HTTPException(status_code=500, detail="Failed to fetch post")

def update_post(db: Session, post_id: int, post_data: PostUpdate):
    try:
        post = db.query(Post).filter(
            Post.id == post_id, Post.deleted_at.is_(None)
        ).first()

        if not post:
            return None

        update_data = post_data.dict(exclude_unset=True)

        if "title" in update_data:
            post.title = update_data["title"]

        if "content" in update_data:
            post.content = update_data["content"]
        if "image_url" in update_data:
            post.image_url = update_data["image_url"]  
        post.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(post)
        return post
    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error updating post:", e)
        raise HTTPException(status_code=500, detail="Failed to update post")

    except Exception as e:
        db.rollback()
        print("Unexpected error updating post:", e)
        raise HTTPException(status_code=500, detail="Failed to update post")


def delete_post(db: Session, post_id: int):
    try:
        post = db.query(Post).filter(
            Post.id == post_id, Post.deleted_at.is_(None)
        ).first()

        if not post:
            return False

        now = datetime.now(timezone.utc)
        post.deleted_at = now
        post.status = False
        comments = db.query(Comment).filter(
            Comment.post_id == post_id, Comment.deleted_at.is_(None)
        ).all()

        for c in comments:
            c.deleted_at = now

        db.commit()
        return True

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error deleting post:", e)
        raise HTTPException(status_code=500, detail="Failed to delete post")

    except Exception as e:
        db.rollback()
        print("Unexpected error deleting post:", e)
        raise HTTPException(status_code=500, detail="Failed to delete post")


def add_comment_to_post(db: Session, comment: CommentCreate, user_id: int):
    try:
        new_comment = Comment(
            post_id=comment.post_id,
            user_id=user_id,
            comment_text=comment.comment_text,
        )
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)
        return new_comment

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error adding comment:", e)
        raise HTTPException(status_code=500, detail="Failed to add comment")

    except Exception as e:
        db.rollback()
        print("Unexpected error adding comment:", e)
        raise HTTPException(status_code=500, detail="Failed to add comment")


def delete_comment(db: Session, comment_id: int):
    try:
        comment = db.query(Comment).filter(
            Comment.id == comment_id, Comment.deleted_at.is_(None)
        ).first()

        if not comment:
            return False

        comment.deleted_at = datetime.now(timezone.utc)
        comment.status = False
        db.commit()
        return True

    except SQLAlchemyError as e:
        db.rollback()
        print("DB Error deleting comment:", e)
        raise HTTPException(status_code=500, detail="Failed to delete comment")

    except Exception as e:
        db.rollback()
        print("Unexpected error deleting comment:", e)
        raise HTTPException(status_code=500, detail="Failed to delete comment")


def get_user_posts(db: Session, user_id: int):
    try:
        return (
            db.query(Post)
            .filter(Post.user_id == user_id, Post.deleted_at.is_(None))
            .order_by(Post.created_at.desc())
            .all()
        )
    except SQLAlchemyError as e:
        print("DB Error fetching user posts:", e)
        raise HTTPException(status_code=500, detail="Failed to fetch user posts")


def get_comments_for_post(db: Session, post_id: int):
    try:
        return (
            db.query(Comment)
            .filter(Comment.post_id == post_id, Comment.deleted_at.is_(None))
            .order_by(Comment.created_at.asc())
            .all()
        )
    except SQLAlchemyError as e:
        print("DB Error fetching comments:", e)
        raise HTTPException(status_code=500, detail="Failed to fetch comments")