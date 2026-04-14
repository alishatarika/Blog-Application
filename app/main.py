from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import Base, engine
from app.routers.login_controller import router
from app.routers.registration_controller import router as registration
from app.routers.post_controller import router as post
import app.models
from app.routers.auth_controller import router as auth_api

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)
app.add_middleware(
    SessionMiddleware,
    secret_key="secret" 
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