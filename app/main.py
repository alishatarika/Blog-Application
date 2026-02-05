from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.database.connection import Base, engine
from app.routers.login_controller import router
from app.routers.registration_controller import router as registration
from app.routers.post_controller import router as post
import app.models
from app.helper.auth_api import router as auth_api

app = FastAPI()


app.add_middleware(
    SessionMiddleware,
    secret_key="secret"  # Change this to a secure secret key in production
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(router)
app.include_router(registration)
app.include_router(post)
app.include_router(auth_api)
# Create all database tables
Base.metadata.create_all(bind=engine)