from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.database.connection import get_db
from app.helper.dependencies import get_current_user, get_current_user_optional
from app.schemas.post import PostCreate, PostUpdate
from app.schemas.comment import CommentCreate
from app.models.comments import Comment
from app.services.post_service import (
    create_post,
    get_post_by_id,
    update_post,
    delete_post,
    add_comment_to_post,
    delete_comment,
    get_user_posts,
    get_all_posts,
)
import os
from typing import Optional
from app.helper.imagefile import save_upload_file,delete_file_if_exists


router = APIRouter()
templates = Jinja2Templates(directory="templates")



# ================= HOME =================
@router.get("/read", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    try:
        posts = get_all_posts(db)
        posts_data = [post.to_dict() for post in posts]
        # print(f"{posts_data}:::::")
        return templates.TemplateResponse(
            "home.html",
            {"request": request, "posts": posts_data, "current_user": user},
        )
    except HTTPException:
        raise
    except Exception as e:
        print("Error loading home page:", e)
        raise HTTPException(status_code=500, detail="Failed to load posts")

# ================= CREATE POST =================
@router.get("/create-post", response_class=HTMLResponse)
def create_post_page(request: Request, user=Depends(get_current_user)):
    try:
        return templates.TemplateResponse(
            "create_post.html",
            {"request": request, "current_user": user},
        )
    except HTTPException:
        raise
    except Exception as e:
        print("Error rendering create-post page:", e)
        raise HTTPException(status_code=500, detail="Failed to load page")

@router.post("/create-post", response_class=RedirectResponse)
def create_post_action(
    title: str = Form(...),
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        image_url = None
        if image and image.filename:
            image_url = save_upload_file(image)

        post_data = PostCreate(title=title, content=content, image_url=image_url)
        create_post(db, post_data, user.id)
        return RedirectResponse("/read", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error creating post:", e)
        raise HTTPException(status_code=500, detail="Failed to create post")

# ================= EDIT POST =================
@router.get("/post/{post_id}/edit", response_class=HTMLResponse)
def edit_post_page(post_id: int, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        post = get_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        return templates.TemplateResponse(
            "edit_post.html",
            {"request": request, "post": post, "current_user": user},
        )
    except HTTPException:
        raise
    except Exception as e:
        print("Error rendering edit-post page:", e)
        raise HTTPException(status_code=500, detail="Failed to load page")

@router.post("/post/{post_id}/edit", response_class=RedirectResponse)
def update_post_action(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    remove_image: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        post = get_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        old_image = post.image_url

        if remove_image == "true":
            image_url = None
            delete_file_if_exists(old_image)
        elif image and image.filename:
            image_url = save_upload_file(image)
            delete_file_if_exists(old_image)
        else:
            image_url = old_image

        post_data = PostUpdate(title=title, content=content, image_url=image_url)
        update_post(db, post_id, post_data)
        return RedirectResponse("/read", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error updating post:", e)
        raise HTTPException(status_code=500, detail="Failed to update post")

# ================= DELETE POST =================
@router.post("/post/{post_id}/delete", response_class=RedirectResponse)
def delete_post_action(post_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        post = get_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        delete_file_if_exists(post.image_url)

        delete_post(db, post_id)

        return RedirectResponse("/read", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error deleting post:", e)
        raise HTTPException(status_code=500, detail="Failed to delete post")

# ================= COMMENTS =================
@router.post("/post/{post_id}/comment", response_class=RedirectResponse)
def add_comment(post_id: int, comment_text: str = Form(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        comment_data = CommentCreate(post_id=post_id, comment_text=comment_text)
        add_comment_to_post(db, comment_data, user.id)
        return RedirectResponse("/read", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error adding comment:", e)
        raise HTTPException(status_code=500, detail="Failed to add comment")

@router.post("/comment/{comment_id}/delete", response_class=RedirectResponse)
def delete_comment_action(comment_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        post = get_post_by_id(db, comment.post_id)
        if comment.user_id != user.id and post.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        delete_comment(db, comment_id)
        return RedirectResponse("/read", status_code=303)
    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error deleting comment:", e)
        raise HTTPException(status_code=500, detail="Failed to delete comment")

# ================= PROFILE =================
@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        user_posts = get_user_posts(db, user.id)
        for post in user_posts:
            post.comments = [c for c in post.comments if c.deleted_at is None]
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": user,
                "posts": user_posts,
                "current_user": user,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        print("Error loading profile page:", e)
        raise HTTPException(status_code=500, detail="Failed to load profile")
