from fastapi import APIRouter

router = APIRouter()

from app.api.v1.endpoints import analyze, redact

router.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
router.include_router(redact.router, prefix="/redact", tags=["redact"])