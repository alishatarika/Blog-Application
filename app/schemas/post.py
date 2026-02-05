from pydantic import BaseModel 
from datetime import datetime
from typing import Optional

class PostCreate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None  
class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None  