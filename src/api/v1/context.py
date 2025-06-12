"""Context management endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_auth_context, AuthContext
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.context import Context
from src.services.base import BaseService


logger = get_logger(__name__)
router = APIRouter()


class ContextCreate(BaseModel):
    """Context creation model."""
    
    namespace: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=1, max_length=100)
    value: dict
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[dict] = Field(default_factory=dict)


class ContextUpdate(BaseModel):
    """Context update model."""
    
    value: Optional[dict] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class ContextResponse(BaseModel):
    """Context response model."""
    
    id: UUID
    namespace: str
    key: str
    value: dict
    tags: List[str]
    metadata: dict
    created_at: datetime
    updated_at: datetime
    tenant_id: UUID


@router.post(
    "/",
    response_model=ContextResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store context",
    description="Store a new context in the specified namespace",
)
async def create_context(
    context: ContextCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> ContextResponse:
    """Create a new context."""
    logger.info(f"Creating context in {context.namespace}/{context.key}")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    # Check if context already exists
    result = await db.execute(
        select(Context).where(
            and_(
                Context.tenant_id == auth.tenant_id,
                Context.namespace == context.namespace,
                Context.key == context.key
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Context already exists: {context.namespace}/{context.key}"
        )
    
    # Create context
    new_context = Context(
        tenant_id=auth.tenant_id,
        namespace=context.namespace,
        key=context.key,
        value=context.value,
        tags=context.tags,
        metadata=context.metadata,
        created_by=auth.user_id,
        updated_by=auth.user_id
    )
    
    db.add(new_context)
    await db.commit()
    await db.refresh(new_context)
    
    return ContextResponse(
        id=new_context.id,
        namespace=new_context.namespace,
        key=new_context.key,
        value=new_context.value,
        tags=new_context.tags or [],
        metadata=new_context.metadata or {},
        created_at=new_context.created_at,
        updated_at=new_context.updated_at,
        tenant_id=new_context.tenant_id
    )


@router.get(
    "/{namespace}/{key}",
    response_model=ContextResponse,
    summary="Get context",
    description="Retrieve a specific context by namespace and key",
)
async def get_context(
    namespace: str,
    key: str,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> ContextResponse:
    """Get context by namespace and key."""
    logger.info(f"Getting context: {namespace}/{key}")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    result = await db.execute(
        select(Context).where(
            and_(
                Context.tenant_id == auth.tenant_id,
                Context.namespace == namespace,
                Context.key == key
            )
        )
    )
    context = result.scalar_one_or_none()
    
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context not found: {namespace}/{key}"
        )
    
    return ContextResponse(
        id=context.id,
        namespace=context.namespace,
        key=context.key,
        value=context.value,
        tags=context.tags or [],
        metadata=context.metadata or {},
        created_at=context.created_at,
        updated_at=context.updated_at,
        tenant_id=context.tenant_id
    )


@router.get(
    "/{namespace}",
    response_model=List[ContextResponse],
    summary="List contexts",
    description="List all contexts in a namespace",
)
async def list_contexts(
    namespace: str,
    tags: Optional[List[str]] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> List[ContextResponse]:
    """List contexts in a namespace."""
    logger.info(f"Listing contexts in namespace: {namespace}")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    # Build query
    query = select(Context).where(
        and_(
            Context.tenant_id == auth.tenant_id,
            Context.namespace == namespace
        )
    )
    
    # Filter by tags if provided
    if tags:
        # Use PostgreSQL's @> operator for array containment
        query = query.where(Context.tags.contains(tags))
    
    # Add ordering and pagination
    query = query.order_by(Context.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    contexts = result.scalars().all()
    
    return [
        ContextResponse(
            id=ctx.id,
            namespace=ctx.namespace,
            key=ctx.key,
            value=ctx.value,
            tags=ctx.tags or [],
            metadata=ctx.metadata or {},
            created_at=ctx.created_at,
            updated_at=ctx.updated_at,
            tenant_id=ctx.tenant_id
        )
        for ctx in contexts
    ]


@router.put(
    "/{namespace}/{key}",
    response_model=ContextResponse,
    summary="Update context",
    description="Update an existing context",
)
async def update_context(
    namespace: str,
    key: str,
    update: ContextUpdate,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> ContextResponse:
    """Update a context."""
    logger.info(f"Updating context: {namespace}/{key}")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    # Get existing context
    result = await db.execute(
        select(Context).where(
            and_(
                Context.tenant_id == auth.tenant_id,
                Context.namespace == namespace,
                Context.key == key
            )
        )
    )
    context = result.scalar_one_or_none()
    
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context not found: {namespace}/{key}"
        )
    
    # Update fields
    if update.value is not None:
        context.value = update.value
    if update.tags is not None:
        context.tags = update.tags
    if update.metadata is not None:
        context.metadata = update.metadata
    
    context.updated_by = auth.user_id
    context.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(context)
    
    return ContextResponse(
        id=context.id,
        namespace=context.namespace,
        key=context.key,
        value=context.value,
        tags=context.tags or [],
        metadata=context.metadata or {},
        created_at=context.created_at,
        updated_at=context.updated_at,
        tenant_id=context.tenant_id
    )


@router.delete(
    "/{namespace}/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete context",
    description="Delete a specific context",
)
async def delete_context(
    namespace: str,
    key: str,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """Delete a context."""
    logger.info(f"Deleting context: {namespace}/{key}")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    # Get context
    result = await db.execute(
        select(Context).where(
            and_(
                Context.tenant_id == auth.tenant_id,
                Context.namespace == namespace,
                Context.key == key
            )
        )
    )
    context = result.scalar_one_or_none()
    
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context not found: {namespace}/{key}"
        )
    
    await db.delete(context)
    await db.commit()
    
    return None