from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from core.database import db
from core.deps import get_current_user
from core.models import utcnow_iso
from features.projects.models import Project, ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


class BulkDelete(BaseModel):
    ids: List[str]


class EstanciasPayload(BaseModel):
    estancias: list = []
    plantas: Optional[list] = None


_BASE_STR = ("id", "nombre", "planta", "uso_ocupacion")
_BASE_NUM = ("sup_util", "sup_construida", "altura", "densidad", "ocupacion_manual")
_BASE_BOOL = ("sin_ocupacion", "ocupacion_custom")


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _norm_estancia(e: dict) -> dict:
    e = e or {}
    out = {k: ((e.get(k) or "").strip() if isinstance(e.get(k), str) else (e.get(k) or "")) for k in _BASE_STR}
    for k in _BASE_NUM:
        out[k] = _f(e.get(k))
    for k in _BASE_BOOL:
        out[k] = bool(e.get(k))
    return out


def _norm_planta(p: dict) -> dict:
    p = p or {}
    rasante = p.get("rasante")
    return {
        "id": p.get("id"),
        "nombre": (p.get("nombre") or "").strip() if isinstance(p.get("nombre"), str) else (p.get("nombre") or ""),
        "rasante": rasante if rasante in ("sobre", "bajo") else "sobre",
        "altura": _f(p.get("altura")),
    }


def _serialize(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("")
async def list_projects(user: dict = Depends(get_current_user)):
    pipeline = [
        {"$sort": {"created_at": -1}},
        {"$limit": 1000},
        {"$addFields": {"_idstr": {"$toString": "$_id"}}},
        {"$lookup": {"from": "studies", "localField": "_idstr",
                     "foreignField": "project_id", "as": "_studies"}},
        {"$addFields": {"studies_count": {"$size": "$_studies"}}},
        {"$project": {"_studies": 0, "_idstr": 0, "estancias": 0}},
    ]
    docs = await db.projects.aggregate(pipeline).to_list(1000)
    return [_serialize(d) for d in docs]


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
    return {"estancias": doc.get("estancias", []), "plantas": doc.get("plantas", [])}


@router.put("/{project_id}/estancias")
async def put_estancias(project_id: str, payload: EstanciasPayload,
                        user: dict = Depends(get_current_user)):
    existing = await db.projects.find_one({"_id": ObjectId(project_id)},
                                          {"estancias": 1, "plantas": 1, "estancias_updated_at": 1})
    if not existing:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    normalized = [_norm_estancia(e) for e in payload.estancias]
    prev = [_norm_estancia(e) for e in (existing.get("estancias") or [])]
    now = utcnow_iso()
    changed = normalized != prev
    updates = {"estancias": normalized, "updated_at": now}

    plantas_norm = existing.get("plantas", [])
    if payload.plantas is not None:
        plantas_norm = [_norm_planta(p) for p in payload.plantas]
        if plantas_norm != [_norm_planta(p) for p in (existing.get("plantas") or [])]:
            changed = True
        updates["plantas"] = plantas_norm

    if changed:
        updates["estancias_updated_at"] = now
    await db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": updates})
    version = now if changed else existing.get("estancias_updated_at")
    return {"estancias": normalized, "plantas": plantas_norm, "estancias_updated_at": version, "changed": changed}


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
