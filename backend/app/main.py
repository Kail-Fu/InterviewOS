from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.assessment import legacy_router, router as assessment_router
from app.api.dashboard import router as dashboard_router
from app.api.invite import router as invite_router
from app.core.config import get_settings
from app.services.assessment_store import init_assessment_store
from app.services.invite_store import init_store as init_invite_store

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

assets_dir = Path(settings.local_assets_dir)
assets_dir.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

Path(settings.local_submissions_dir).mkdir(parents=True, exist_ok=True)
Path(settings.local_recordings_dir).mkdir(parents=True, exist_ok=True)
Path(settings.local_db_path).parent.mkdir(parents=True, exist_ok=True)
init_invite_store(settings)
init_assessment_store(settings)

app.include_router(assessment_router)
app.include_router(legacy_router)
app.include_router(invite_router)
app.include_router(dashboard_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
