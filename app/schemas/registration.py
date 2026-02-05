from pydantic import BaseModel, EmailStr, validator, Field
import re

class RegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str

    @validator("username")
    def username_valid(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 20:
            raise ValueError("Username must not exceed 20 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v

    @validator("email")
    def email_valid(cls, v):
        v = v.lower().strip()
    
        if not v:
            raise ValueError("Email cannot be empty")
        
        if v.count('@') != 1:
            raise ValueError("Email must contain exactly one @ symbol")
        
        local, domain = v.split('@')
        
        if not local or not domain:
            raise ValueError("Invalid email format")
        
        if len(local) > 64:
            raise ValueError("Email local part is too long")
        
        if '.' not in domain:
            raise ValueError("Email domain must contain a dot")
        
        domain_parts = domain.split('.')
        if any(len(part) == 0 for part in domain_parts):
            raise ValueError("Invalid email domain format")
        if not re.match(r'^[a-zA-Z0-9.-]+$', domain):
            raise ValueError("Email domain contains invalid characters")
        
        if len(domain_parts[-1]) < 2:
            raise ValueError("Invalid email domain extension")
  
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", v):
            raise ValueError("Invalid email format")
        
        if '..' in v:
            raise ValueError("Email cannot contain consecutive dots")
        
        if local.startswith('.') or local.endswith('.'):
            raise ValueError("Email local part cannot start or end with a dot")
        
        return v

    @validator("password")
    def password_strength(cls, v):
        if not v:
            raise ValueError("Password cannot be empty")
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*)")
        return v

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v