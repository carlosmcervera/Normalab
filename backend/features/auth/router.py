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
from features.auth.models import LoginRequest, RegisterRequest, User

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
        "created_at": user.get("created_at"),
    }


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
async def list_users(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Requiere rol administrador")
    users = await db.users.find().to_list(500)
    return [_public(u) for u in users]
