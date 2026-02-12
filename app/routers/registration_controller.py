from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.registration import RegisterSchema
from app.services.registration import register_user_service
from app.services.user_service import delete_user_account
from app.services.otp_service import create_and_send_otp, verify_otp, is_email_verified
from app.helper.dependencies import get_current_user_optional, get_current_user
from pydantic import ValidationError
from fastapi.templating import Jinja2Templates
from app.models.user import User
from app.utils.jwt_handler import create_access_token

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def add_no_cache_headers(response):
    """Add headers to prevent caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/register")
def register_page(request: Request, user=Depends(get_current_user_optional)):
    try:
        if user:
            return RedirectResponse("/read", status_code=303)

        response = templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": {}, "values": {}, "show_otp": False},
        )
        return add_no_cache_headers(response)
    except HTTPException:
        raise
    except Exception as e:
        print("Error rendering registration page:", e)
        raise HTTPException(status_code=500, detail="Failed to load page")


@router.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    errors = {}
    values = {"username": username, "email": email,"password":password,"confirm_password":confirm_password}

    try:
        user_data = RegisterSchema(
            username=username,
            email=email,
            password=password,
            confirm_password=confirm_password,
        )
        
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            errors["username"] = "This username is already taken"
            response = templates.TemplateResponse(
                "register.html",
                {"request": request, "errors": errors, "values": values, "show_otp": False},
            )
            return add_no_cache_headers(response)
        
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            errors["email"] = "This email is already registered"
            response = templates.TemplateResponse(
                "register.html",
                {"request": request, "errors": errors, "values": values, "show_otp": False},
            )
            return add_no_cache_headers(response)
        
        otp_sent = create_and_send_otp(db, user_data.email)
        
        if not otp_sent:
            errors["general"] = "Failed to send verification email. Please try again."
            response = templates.TemplateResponse(
                "register.html",
                {"request": request, "errors": errors, "values": values, "show_otp": False},
            )
            return add_no_cache_headers(response)
        
        # Store registration data in session
        request.session['pending_registration'] = {
            'username': username,
            'email': email,
            'password': password
        }
        
        response = templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "errors": {},
                "values": values,
                "show_otp": True,
            },
        )
        return add_no_cache_headers(response)

    except ValidationError as e:
        for error in e.errors():
            field = error["loc"][0]
            errors[field] = error["msg"]

        response = templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": errors, "values": values, "show_otp": False},
        )
        return add_no_cache_headers(response)

    except HTTPException as e:
        detail = e.detail if hasattr(e, "detail") else str(e)
        errors["general"] = detail

        response = templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": errors, "values": values, "show_otp": False},
        )
        return add_no_cache_headers(response)

    except Exception as e:
        print("Unexpected error during registration:", e)
        errors["general"] = "Something went wrong. Please try again."

        response = templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": errors, "values": values, "show_otp": False},
        )
        return add_no_cache_headers(response)


@router.post("/verify-otp", response_class=HTMLResponse)
def verify_otp_and_register(
    request: Request,
    otp: str = Form(...),
    db: Session = Depends(get_db),
):
    errors = {}

    pending_data = request.session.get('pending_registration')
    if not pending_data:
        return RedirectResponse("/register", status_code=303)

    username = pending_data.get('username')
    email = pending_data.get('email')
    password = pending_data.get('password')

    values = {"username": username, "email": email}

    try:
        is_valid = verify_otp(db, email, otp)
        if not is_valid:
            errors["otp"] = "Invalid or expired OTP. Please try again."
            response = templates.TemplateResponse(
                "register.html",
                {"request": request, "errors": errors, "values": values, "show_otp": True},
            )
            return add_no_cache_headers(response)

        user_data = RegisterSchema(
            username=username,
            email=email,
            password=password,
            confirm_password=password,
        )
        user = register_user_service(db, user_data)   

        request.session.pop('pending_registration', None)

        token = create_access_token({"user_id": user.id})
        response = RedirectResponse(url="/read", status_code=303)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=60 * 60 * 24 * 7  
        )

        return response

    except Exception as e:
        print("Unexpected error during OTP verification:", e)
        errors["general"] = "Something went wrong. Please try again."

        response = templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": errors, "values": values, "show_otp": True},
        )
        return add_no_cache_headers(response)
