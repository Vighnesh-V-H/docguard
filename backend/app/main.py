from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db


settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting DocGuard AI API")
    await init_db()
    yield
    logger.info("Shutting down DocGuard AI API")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME, "version": "1.0.0"}


@app.get("/")
async def root():
    return {"service": settings.APP_NAME, "version": "1.0.0", "docs": "/docs"}


from app.api.v1 import router as api_v1_router

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)