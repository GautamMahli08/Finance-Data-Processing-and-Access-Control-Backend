from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from app.models.enums import Role
import re

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role = Role.viewer

    @field_validator("password")
    @classmethod
    def strong_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[@$!%*#?&]", v):
            raise ValueError("Password must contain at least one special character (@$!%*#?&)")
        return v

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()

class UserUpdate(BaseModel):
    name:      Optional[str]  = None
    role:      Optional[Role] = None
    is_active: Optional[bool] = None

class UserOut(BaseModel):
    id:         str
    name:       str
    email:      str
    role:       Role
    is_active:  bool
    created_at: str

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserOut

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[@$!%*#?&]", v):
            raise ValueError("Password must contain at least one special character")
        return v
