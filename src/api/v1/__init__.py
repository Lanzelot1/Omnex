"""API v1 endpoints."""

from fastapi import APIRouter

from src.api.v1 import auth, context, memory

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(context.router, prefix="/context", tags=["context"])
router.include_router(memory.router, prefix="/memory", tags=["memory"])