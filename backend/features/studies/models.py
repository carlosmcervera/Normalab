from typing import Any, Optional
from pydantic import BaseModel, Field

from core.models import BaseDocument, utcnow_iso


class Study(BaseDocument):
    project_id: str
    module_code: str
    name: str
    status: str = "borrador"  # borrador | calculado
    data: dict = Field(default_factory=dict)
    results: Optional[dict] = None
    report: Optional[dict] = None
    current_version: int = 0
    created_by: str
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)


class StudyCreate(BaseModel):
    project_id: str
    module_code: str
    name: str = Field(min_length=1)


class StudyUpdate(BaseModel):
    name: Optional[str] = None
    data: Optional[dict] = None


class StudyVersion(BaseDocument):
    study_id: str
    version: int
    data: dict
    results: dict
    report: dict
    note: Optional[str] = None
    created_by: str
    created_at: str = Field(default_factory=utcnow_iso)
