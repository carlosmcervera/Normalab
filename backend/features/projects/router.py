from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from core.database import db
from core.deps import get_current_user
from core.models import utcnow_iso
from features.projects.models import Project, ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


class BulkDelete(BaseModel):
    ids: List[str]


class EstanciasPayload(BaseModel):
    estancias: list = []


def _serialize(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("")
async def list_projects(user: dict = Depends(get_current_user)):
    docs = await db.projects.find().sort("created_at", -1).to_list(1000)
    result = []
    for d in docs:
        count = await db.studies.count_documents({"project_id": str(d["_id"])})
        item = _serialize(d)
        item["studies_count"] = count
        result.append(item)
    return result


@router.post("")
async def create_project(payload: ProjectCreate, user: dict = Depends(get_current_user)):
    project = Project(owner_id=user["_id"], **payload.model_dump())
    result = await db.projects.insert_one(project.to_mongo())
    doc = await db.projects.find_one({"_id": result.inserted_id})
    return _serialize(doc)


@router.get("/{project_id}")
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    doc = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return _serialize(doc)


@router.put("/{project_id}")
async def update_project(project_id: str, payload: ProjectUpdate,
                         user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = utcnow_iso()
    result = await db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    doc = await db.projects.find_one({"_id": ObjectId(project_id)})
    return _serialize(doc)


@router.get("/{project_id}/estancias")
async def get_estancias(project_id: str, user: dict = Depends(get_current_user)):
    doc = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return {"estancias": doc.get("estancias", [])}


@router.put("/{project_id}/estancias")
async def put_estancias(project_id: str, payload: EstanciasPayload,
                        user: dict = Depends(get_current_user)):
    result = await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {"estancias": payload.estancias, "updated_at": utcnow_iso()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return {"estancias": payload.estancias}


@router.post("/bulk-delete")
async def bulk_delete_projects(payload: BulkDelete, user: dict = Depends(get_current_user)):
    oids = [ObjectId(i) for i in payload.ids if ObjectId.is_valid(i)]
    if not oids:
        raise HTTPException(status_code=400, detail="No se han indicado expedientes válidos.")
    str_ids = [str(o) for o in oids]
    await db.studies.delete_many({"project_id": {"$in": str_ids}})
    result = await db.projects.delete_many({"_id": {"$in": oids}})
    return {"ok": True, "deleted": result.deleted_count}


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    await db.studies.delete_many({"project_id": project_id})
    result = await db.projects.delete_one({"_id": ObjectId(project_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return {"ok": True}
