from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.user_service import authenticate_user
from app.utils.jwt_handler import create_access_token
from app.helper.dependencies import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def render_login_template(
    request: Request,
    errors: dict = None,
    values: dict = None,
    success: str = None
):
    context = {
        "request": request,
        "errors": errors or {},
        "values": values or {}
    }

    if success:
        context["success"] = success
    if errors and "general" in errors:
        context["error"] = errors["general"]
    
    return templates.TemplateResponse("login.html", context)


# ---------------- WELCOME PAGE ----------------
@router.get("/", response_class=HTMLResponse)
def welcome_page(request: Request, user=Depends(get_current_user_optional)):
    """Display welcome/landing page"""
    return templates.TemplateResponse(
        "welcomepage.html",
        {"request": request, "current_user": user},
    )


# ---------------- LOGIN PAGE ----------------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user=Depends(get_current_user_optional)):
    """Display login page"""
    try:
        if user:
            return RedirectResponse("/read", status_code=303)
        verified = request.query_params.get("verified")
        success = "✅ Account verified! Please log in." if verified else None

        return render_login_template(request, success=success)
    
    except HTTPException:
        raise
    except Exception as e:
        print("Error rendering login page:", e)
        raise HTTPException(status_code=500, detail="Failed to load page")


# ---------------- LOGIN LOGIC ----------------
@router.post("/login")
def login_user(
    request: Request,
    identifier: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    db: Session = Depends(get_db),
):
    """
    Handle user login with proper error handling and data preservation.
    Preserves identifier (username/email) on error but never sends password back.
    """
    errors = {}
    values = {"identifier": identifier}  

    try:
        if not identifier or not identifier.strip():
            errors["identifier"] = "Username or Email is required"
            return render_login_template(request, errors, values)
        
        if not password or len(password) < 6:
            errors["password"] = "Password must be at least 6 characters"
            return render_login_template(request, errors, values)

        user = authenticate_user(db, identifier.strip(), password)

        if not user:
            errors["general"] = "Invalid username/email or password"
            return render_login_template(request, errors, values)
        if not user.status:
            errors["general"] = "Your account has been deactivated"
            return render_login_template(request, errors, values)

        token = create_access_token({"user_id": user.id})
        response = RedirectResponse(url="/read", status_code=303)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            samesite="lax",
            secure=False, 
            max_age=60 * 60 * 24 * 7 if remember else 60 * 30,  
        )

        return response

    except HTTPException as e:
        errors["general"] = e.detail if hasattr(e, "detail") else str(e)
        return render_login_template(request, errors, values)

    except Exception as e:
        print("Unexpected error during login:", e)
        errors["general"] = "Something went wrong. Please try again."
        return render_login_template(request, errors, values)


# ---------------- LOGOUT ----------------
@router.post("/logout")
def logout():
    """Handle user logout"""
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("access_token")
    return response