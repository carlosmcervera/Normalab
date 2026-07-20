from fastapi import APIRouter, Depends, HTTPException

from core.deps import get_current_user
from normative_modules.registry import registry

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("")
async def list_modules(user: dict = Depends(get_current_user)):
    return registry.metas()


@router.get("/{code}")
async def get_module(code: str, user: dict = Depends(get_current_user)):
    mod = registry.get(code)
    if not mod:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    return mod.meta()


@router.get("/{code}/schema")
async def get_module_schema(code: str, user: dict = Depends(get_current_user)):
    mod = registry.get(code)
    if not mod:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    schema = mod.get_schema()
    if schema is None:
        raise HTTPException(status_code=400, detail="Este módulo no tiene asistente disponible")
    return {"meta": mod.meta(), "schema": schema}
