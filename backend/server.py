from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.database import create_indexes, db
from core.security import hash_password, verify_password
from normative_modules.registry import bootstrap_modules

from features.auth.router import router as auth_router
from features.projects.router import router as projects_router
from features.studies.router import router as studies_router
from features.modules import router as modules_router

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="NormaLab API", version="1.0.0")
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "NormaLab API", "status": "ok"}


@api_router.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(studies_router)
api_router.include_router(modules_router)
app.include_router(api_router)


@app.get("/health")
async def k8s_health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@normalab.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin1234!")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email, "password_hash": hash_password(admin_password),
            "name": "Administrador", "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Admin creado: %s", admin_email)
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email},
                                  {"$set": {"password_hash": hash_password(admin_password)}})


@app.on_event("startup")
async def on_startup():
    await create_indexes()
    await seed_admin()
    bootstrap_modules()
    logger.info("Módulos normativos registrados: %s",
                [m.code for m in __import__("normative_modules.registry",
                                            fromlist=["registry"]).registry.all()])


@app.on_event("shutdown")
async def on_shutdown():
    from core.database import client
    client.close()
