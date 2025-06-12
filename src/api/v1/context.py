"""Context management endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter()


class ContextCreate(BaseModel):
    """Context creation model."""
    
    namespace: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=1, max_length=100)
    value: dict
    tags: Optional[List[str]] = Field(default_factory=list)


class ContextResponse(BaseModel):
    """Context response model."""
    
    id: str
    namespace: str
    key: str
    value: dict
    tags: List[str]
    created_at: datetime
    updated_at: datetime


@router.post(
    "/",
    response_model=ContextResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store context",
    description="Store a new context in the specified namespace",
)
async def create_context(context: ContextCreate) -> ContextResponse:
    """Create a new context."""
    logger.info("Creating context", namespace=context.namespace, key=context.key)
    
    # Mock implementation
    return ContextResponse(
        id="ctx_123456",
        namespace=context.namespace,
        key=context.key,
        value=context.value,
        tags=context.tags,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get(
    "/{namespace}/{key}",
    response_model=ContextResponse,
    summary="Get context",
    description="Retrieve a specific context by namespace and key",
)
async def get_context(namespace: str, key: str) -> ContextResponse:
    """Get context by namespace and key."""
    logger.info("Getting context", namespace=namespace, key=key)
    
    # Mock implementation
    return ContextResponse(
        id="ctx_123456",
        namespace=namespace,
        key=key,
        value={"example": "data"},
        tags=["example", "test"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.get(
    "/{namespace}",
    response_model=List[ContextResponse],
    summary="List contexts",
    description="List all contexts in a namespace",
)
async def list_contexts(
    namespace: str,
    tags: Optional[List[str]] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[ContextResponse]:
    """List contexts in a namespace."""
    logger.info("Listing contexts", namespace=namespace, tags=tags)
    
    # Mock implementation
    return [
        ContextResponse(
            id=f"ctx_{i}",
            namespace=namespace,
            key=f"key_{i}",
            value={"index": i},
            tags=tags or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        for i in range(min(3, limit))
    ]


@router.delete(
    "/{namespace}/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete context",
    description="Delete a specific context",
)
async def delete_context(namespace: str, key: str):
    """Delete a context."""
    logger.info("Deleting context", namespace=namespace, key=key)
    # Mock implementation
    return None