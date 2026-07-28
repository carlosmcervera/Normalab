from datetime import datetime, timezone, timedelta
import secrets
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.database import db
from core.deps import get_current_user
from core.models import utcnow
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from features.auth.models import (
    AdminCreateUser, AdminResetPassword, AdminUpdateUser, LoginRequest, RegisterRequest, User,
)

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _set_auth_cookies(response: Response, user_id: str, email: str):
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id)
    response.set_cookie("access_token", access, httponly=True, secure=False,
                        samesite="lax", max_age=900, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=False,
                        samesite="lax", max_age=604800, path="/")


def _public(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user.get("role", "tecnico"),
        "active": user.get("active", True),
        "created_at": user.get("created_at"),
    }


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Requiere rol administrador")
    return user


async def _count_active_admins(exclude_id: str | None = None) -> int:
    q = {"role": "admin", "active": {"$ne": False}}
    if exclude_id:
        q["_id"] = {"$ne": ObjectId(exclude_id)}
    return await db.users.count_documents(q)


@router.post("/register")
async def register(payload: RegisterRequest, response: Response):
    email = payload.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    user = User(email=email, password_hash=hash_password(payload.password),
                name=payload.name, role=payload.role)
    result = await db.users.insert_one(user.to_mongo())
    uid = str(result.inserted_id)
    _set_auth_cookies(response, uid, email)
    created = await db.users.find_one({"_id": result.inserted_id})
    return _public(created)


@router.post("/login")
async def login(payload: LoginRequest, request: Request, response: Response):
    email = payload.email.lower()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"
    attempt = await db.login_attempts.find_one({"identifier": identifier})
    if attempt and attempt.get("count", 0) >= MAX_ATTEMPTS:
        locked_until = attempt.get("locked_until")
        if locked_until and datetime.fromisoformat(locked_until) > utcnow():
            raise HTTPException(status_code=429, detail="Demasiados intentos. Inténtalo más tarde.")

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        count = (attempt.get("count", 0) if attempt else 0) + 1
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$set": {"identifier": identifier, "count": count,
                      "locked_until": (utcnow() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
                      if count >= MAX_ATTEMPTS else None}},
            upsert=True,
        )
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    await db.login_attempts.delete_one({"identifier": identifier})
    if user.get("active") is False:
        raise HTTPException(status_code=403, detail="Cuenta desactivada. Contacta con un administrador.")
    _set_auth_cookies(response, str(user["_id"]), email)
    return _public(user)


@router.post("/logout")
async def logout(response: Response, user: dict = Depends(get_current_user)):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return _public({**user, "_id": user["_id"]})


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No hay token de refresco")
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Tipo de token inválido")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        access = create_access_token(str(user["_id"]), user["email"])
        response.set_cookie("access_token", access, httponly=True, secure=False,
                            samesite="lax", max_age=900, path="/")
        return {"ok": True}
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.get("/users")
async def list_users(admin: dict = Depends(require_admin)):
    users = await db.users.find().sort("created_at", 1).to_list(500)
    return [_public(u) for u in users]


@router.post("/users", status_code=201)
async def create_user(payload: AdminCreateUser, admin: dict = Depends(require_admin)):
    email = payload.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    user = User(email=email, password_hash=hash_password(payload.password),
                name=payload.name, role=payload.role, active=True)
    result = await db.users.insert_one(user.to_mongo())
    created = await db.users.find_one({"_id": result.inserted_id})
    return _public(created)


@router.patch("/users/{user_id}")
async def update_user(user_id: str, payload: AdminUpdateUser, admin: dict = Depends(require_admin)):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    target = await db.users.find_one({"_id": oid})
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    is_self = str(target["_id"]) == str(admin["_id"])
    updates: dict = {}
    if payload.name is not None:
        updates["name"] = payload.name

    demoting = payload.role is not None and payload.role != "admin" and target.get("role") == "admin"
    deactivating = payload.active is False and target.get("active", True)

    if is_self and (demoting or deactivating):
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol de administrador ni desactivar tu cuenta.")
    if (demoting or deactivating) and await _count_active_admins(exclude_id=user_id) == 0:
        raise HTTPException(status_code=400, detail="Debe quedar al menos un administrador activo.")

    if payload.role is not None:
        updates["role"] = payload.role
    if payload.active is not None:
        updates["active"] = payload.active

    if updates:
        await db.users.update_one({"_id": oid}, {"$set": updates})
    updated = await db.users.find_one({"_id": oid})
    return _public(updated)


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, payload: AdminResetPassword, admin: dict = Depends(require_admin)):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    target = await db.users.find_one({"_id": oid})
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    await db.users.update_one({"_id": oid}, {"$set": {"password_hash": hash_password(payload.password)}})
    return {"ok": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    target = await db.users.find_one({"_id": oid})
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if str(target["_id"]) == str(admin["_id"]):
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta.")
    if target.get("role") == "admin" and target.get("active", True) and await _count_active_admins(exclude_id=user_id) == 0:
        raise HTTPException(status_code=400, detail="Debe quedar al menos un administrador activo.")
    await db.users.delete_one({"_id": oid})
    return {"ok": True}
