from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field

from core.models import BaseDocument, PyObjectId, utcnow_iso

Role = Literal["admin", "tecnico"]


class User(BaseDocument):
    email: str
    password_hash: str
    name: str
    role: Role = "tecnico"
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
    created_at: Optional[str] = None
