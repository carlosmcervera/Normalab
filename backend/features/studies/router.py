from urllib.parse import quote

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from core.database import db
from core.deps import get_current_user
from core.models import utcnow_iso
from features.studies.exporters import build_docx, build_xlsx
from features.studies.models import Study, StudyCreate, StudyUpdate, StudyVersion
from normative_modules.registry import registry

router = APIRouter(prefix="/studies", tags=["studies"])


def _serialize(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


async def _get_study_or_404(study_id: str) -> dict:
    doc = await db.studies.find_one({"_id": ObjectId(study_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Estudio no encontrado")
    return doc


@router.get("")
async def list_studies(project_id: Optional[str] = None,
                       user: dict = Depends(get_current_user)):
    query = {"project_id": project_id} if project_id else {}
    docs = await db.studies.find(query).sort("updated_at", -1).to_list(1000)
    result = []
    for d in docs:
        item = _serialize(d)
        mod = registry.get(d["module_code"])
        item["module_name"] = mod.short_name if mod else d["module_code"]
        result.append(item)
    return result


@router.post("")
async def create_study(payload: StudyCreate, user: dict = Depends(get_current_user)):
    mod = registry.get(payload.module_code)
    if not mod:
        raise HTTPException(status_code=400, detail="Módulo normativo desconocido")
    if mod.status != "operativo":
        raise HTTPException(status_code=400, detail=f"El módulo {mod.short_name} aún no es operativo")
    project = await db.projects.find_one({"_id": ObjectId(payload.project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    study = Study(created_by=user["_id"], **payload.model_dump())
    result = await db.studies.insert_one(study.to_mongo())
    doc = await db.studies.find_one({"_id": result.inserted_id})
    return _serialize(doc)


@router.get("/{study_id}")
async def get_study(study_id: str, user: dict = Depends(get_current_user)):
    return _serialize(await _get_study_or_404(study_id))


@router.put("/{study_id}")
async def update_study(study_id: str, payload: StudyUpdate,
                       user: dict = Depends(get_current_user)):
    await _get_study_or_404(study_id)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = utcnow_iso()
    await db.studies.update_one({"_id": ObjectId(study_id)}, {"$set": updates})
    doc = await db.studies.find_one({"_id": ObjectId(study_id)})
    return _serialize(doc)


@router.delete("/{study_id}")
async def delete_study(study_id: str, user: dict = Depends(get_current_user)):
    await _get_study_or_404(study_id)
    await db.study_versions.delete_many({"study_id": study_id})
    await db.studies.delete_one({"_id": ObjectId(study_id)})
    return {"ok": True}


@router.post("/{study_id}/compute")
async def compute_study(study_id: str, user: dict = Depends(get_current_user)):
    doc = await _get_study_or_404(study_id)
    mod = registry.get(doc["module_code"])
    if not mod or mod.status != "operativo":
        raise HTTPException(status_code=400, detail="Módulo no operativo")
    project = await db.projects.find_one({"_id": ObjectId(doc["project_id"])})
    try:
        results = mod.compute(doc.get("data") or {})
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    report = mod.build_report(_serialize(project) if project else {}, _serialize(doc),
                              doc.get("data") or {}, results)
    await db.studies.update_one(
        {"_id": ObjectId(study_id)},
        {"$set": {"results": results, "report": report, "status": "calculado",
                  "updated_at": utcnow_iso()}},
    )
    return {"results": results, "report": report}


class VersionNote(BaseModel):
    note: Optional[str] = None


@router.post("/{study_id}/version")
async def create_version(study_id: str, payload: VersionNote,
                         user: dict = Depends(get_current_user)):
    doc = await _get_study_or_404(study_id)
    mod = registry.get(doc["module_code"])
    if not mod or mod.status != "operativo":
        raise HTTPException(status_code=400, detail="Módulo no operativo")
    project = await db.projects.find_one({"_id": ObjectId(doc["project_id"])})
    try:
        results = mod.compute(doc.get("data") or {})
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    report = mod.build_report(_serialize(project) if project else {}, _serialize(doc),
                              doc.get("data") or {}, results)
    new_version = int(doc.get("current_version", 0)) + 1
    version = StudyVersion(study_id=study_id, version=new_version, data=doc.get("data") or {},
                           results=results, report=report, note=payload.note,
                           created_by=user["_id"])
    await db.study_versions.insert_one(version.to_mongo())
    await db.studies.update_one(
        {"_id": ObjectId(study_id)},
        {"$set": {"results": results, "report": report, "status": "calculado",
                  "current_version": new_version, "updated_at": utcnow_iso()}},
    )
    return {"version": new_version, "results": results, "report": report}


@router.get("/{study_id}/versions")
async def list_versions(study_id: str, user: dict = Depends(get_current_user)):
    docs = await db.study_versions.find({"study_id": study_id}).sort("version", -1).to_list(200)
    return [_serialize(d) for d in docs]


@router.get("/{study_id}/versions/{version}")
async def get_version(study_id: str, version: int, user: dict = Depends(get_current_user)):
    doc = await db.study_versions.find_one({"study_id": study_id, "version": version})
    if not doc:
        raise HTTPException(status_code=404, detail="Versión no encontrada")
    return _serialize(doc)


async def _project_for(doc: dict) -> dict:
    project = await db.projects.find_one({"_id": ObjectId(doc["project_id"])})
    return _serialize(project) if project else {}


def _download(buf, filename: str, media_type: str) -> StreamingResponse:
    disp = f"attachment; filename*=UTF-8''{quote(filename)}"
    return StreamingResponse(buf, media_type=media_type, headers={"Content-Disposition": disp})


@router.get("/{study_id}/export/docx")
async def export_docx(study_id: str, user: dict = Depends(get_current_user)):
    doc = await _get_study_or_404(study_id)
    report = doc.get("report")
    if not report:
        raise HTTPException(status_code=400, detail="El estudio aún no tiene informe. Ejecuta el cálculo primero.")
    project = await _project_for(doc)
    buf = build_docx(report, _serialize(doc), project)
    name = f"{project.get('code','estudio')}_{doc.get('name','informe')}.docx".replace(" ", "_")
    return _download(buf, name, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.get("/{study_id}/export/xlsx")
async def export_xlsx(study_id: str, user: dict = Depends(get_current_user)):
    doc = await _get_study_or_404(study_id)
    if not doc.get("results"):
        raise HTTPException(status_code=400, detail="El estudio aún no tiene resultados. Ejecuta el cálculo primero.")
    project = await _project_for(doc)
    buf = build_xlsx(_serialize(doc), project)
    name = f"{project.get('code','estudio')}_{doc.get('name','tablas')}.xlsx".replace(" ", "_")
    return _download(buf, name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
