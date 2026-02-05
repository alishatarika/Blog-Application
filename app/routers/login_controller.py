from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.login import login_user_service
from app.utils.jwt_handler import create_access_token
from app.helper.dependencies import get_current_user_optional
from dotenv import load_dotenv
import os
load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ---------------- WELCOME PAGE ----------------
@router.get("/", response_class=HTMLResponse)
def welcome_page(request: Request, user=Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        "welcomepage.html",
        {"request": request, "current_user": user},
    )


# ---------------- LOGIN PAGE ----------------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user=Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/read", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


# ---------------- LOGIN LOGIC ----------------
@router.post("/login")
def login_user(
    request: Request,
    identifier: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    db: Session = Depends(get_db),
):
    user = login_user_service(db, identifier, password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
        )

    token = create_access_token({"user_id": user.id})

    response = RedirectResponse(url="/read", status_code=303)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  
        max_age=60 * 60 * 24 * 7 if remember else None,
    )

    return response


# ---------------- LOGOUT ----------------
@router.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("access_token")
    return response
