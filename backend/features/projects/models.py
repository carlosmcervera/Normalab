from typing import Optional
from pydantic import BaseModel, Field

from core.models import BaseDocument, utcnow_iso


class Project(BaseDocument):
    code: str
    name: str
    client: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    owner_id: str
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)


class ProjectCreate(BaseModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    client: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    client: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
