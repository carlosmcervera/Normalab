from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field

from core.models import BaseDocument, PyObjectId, utcnow_iso

Role = Literal["admin", "tecnico"]


class User(BaseDocument):
    email: str
    password_hash: str
    name: str
    role: Role = "tecnico"
    active: bool = True
    created_at: str = Field(default_factory=utcnow_iso)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)
    role: Role = "tecnico"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: PyObjectId
    email: str
    name: str
    role: Role
    active: bool = True
    created_at: Optional[str] = None


class AdminCreateUser(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1)
    password: str = Field(min_length=6)
    role: Role = "tecnico"


class AdminUpdateUser(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    role: Optional[Role] = None
    active: Optional[bool] = None


class AdminResetPassword(BaseModel):
    password: str = Field(min_length=6)
