"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.api import health, v1
from src.core.cache import cache
from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.logging import setup_logging, get_logger


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting Omnex v{settings.APP_VERSION}")
    
    # Initialize database
    await init_db()
    
    # Initialize cache
    await cache.connect()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Omnex")
    
    # Close connections
    await cache.disconnect()
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description="Universal memory layer for AI. Share context between ChatGPT, Claude, and any LLM.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Prometheus metrics
if settings.PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(v1.router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Universal memory layer for AI",
        "docs": "/docs",
        "health": "/health",
    }