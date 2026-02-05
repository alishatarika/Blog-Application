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
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/register")
def register_page(request: Request, user=Depends(get_current_user_optional)):
    try:
        if user:
            return RedirectResponse("/read", status_code=303)

        return templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": {}, "values": {}, "show_otp": False},
        )
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
    """Step 1: Validate user data and send OTP"""
    errors = {}
    values = {"username": username, "email": email}

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
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "errors": errors, "values": values, "show_otp": False},
            )
        
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            errors["email"] = "This email is already registered"
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "errors": errors, "values": values, "show_otp": False},
            )
        otp_sent = create_and_send_otp(db, user_data.email)
        
        if not otp_sent:
            errors["general"] = "Failed to send verification email. Please try again."
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "errors": errors, "values": values, "show_otp": False},
            )
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "errors": {},
                "values": values,
                "show_otp": True,
                "user_data": {
                    "username": username,
                    "password": password
                }
            },
        )

    except ValidationError as e:
        for error in e.errors():
            field = error["loc"][0]
            errors[field] = error["msg"]

        return templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": errors, "values": values, "show_otp": False},
        )

    except HTTPException as e:
        detail = e.detail if hasattr(e, "detail") else str(e)
        errors["general"] = detail

        return templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": errors, "values": values, "show_otp": False},
        )

    except Exception as e:
        print("Unexpected error during registration:", e)
        errors["general"] = "Something went wrong. Please try again."

        return templates.TemplateResponse(
            "register.html",
            {"request": request, "errors": errors, "values": values, "show_otp": False},
        )


@router.post("/verify-otp", response_class=HTMLResponse)
def verify_otp_and_register(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    otp: str = Form(...),
    db: Session = Depends(get_db),
):
    """Step 2: Verify OTP and complete registration"""
    errors = {}
    values = {"username": username, "email": email}

    try:
        # Verify OTP
        is_valid = verify_otp(db, email, otp)
        
        if not is_valid:
            errors["otp"] = "Invalid or expired OTP. Please try again."
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "errors": errors,
                    "values": values,
                    "show_otp": True,
                    "user_data": {
                        "username": username,
                        "password": password
                    }
                },
            )
        user_data = RegisterSchema(
            username=username,
            email=email,
            password=password,
            confirm_password=password,
        )
        
        register_user_service(db, user_data)

        return RedirectResponse("/login?verified=true", status_code=303)

    except HTTPException as e:
        detail = e.detail if hasattr(e, "detail") else str(e)
        
        if "Email already registered" in detail:
            errors["email"] = "This email is already registered"
        elif "Username already registered" in detail:
            errors["username"] = "This username is already taken"
        else:
            errors["general"] = "Registration failed. Please try again."

        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "errors": errors,
                "values": values,
                "show_otp": True,
                "user_data": {
                    "username": username,
                    "password": password
                }
            },
        )

    except Exception as e:
        print("Unexpected error during OTP verification:", e)
        errors["general"] = "Something went wrong. Please try again."

        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "errors": errors,
                "values": values,
                "show_otp": True,
                "user_data": {
                    "username": username,
                    "password": password
                }
            },
        )


@router.post("/delete-account")
def delete_account(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        delete_user_account(db, user.id)
        response = RedirectResponse("/", status_code=303)
        response.delete_cookie("access_token")
        return response

    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error during account deletion:", e)
        raise HTTPException(status_code=500, detail="Failed to delete account")