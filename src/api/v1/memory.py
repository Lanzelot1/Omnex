"""Memory management endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_auth_context, AuthContext
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.memory import Memory


logger = get_logger(__name__)
router = APIRouter()


class MemoryCreate(BaseModel):
    """Memory creation model."""
    
    content: str = Field(..., min_length=1)
    metadata: Optional[dict] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class MemoryUpdate(BaseModel):
    """Memory update model."""
    
    content: Optional[str] = None
    metadata: Optional[dict] = None
    embedding: Optional[List[float]] = None


class MemoryResponse(BaseModel):
    """Memory response model."""
    
    id: UUID
    content: str
    metadata: dict
    created_at: datetime
    similarity_score: Optional[float] = None
    tenant_id: UUID


class MemorySearchRequest(BaseModel):
    """Memory search request model."""
    
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)


@router.post(
    "/",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store memory",
    description="Store a new memory with optional embedding",
)
async def create_memory(
    memory: MemoryCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> MemoryResponse:
    """Create a new memory."""
    logger.info(f"Creating memory, content length: {len(memory.content)}")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    # Create memory
    new_memory = Memory(
        tenant_id=auth.tenant_id,
        content=memory.content,
        metadata=memory.metadata,
        embedding=memory.embedding,
        created_by=auth.user_id
    )
    
    db.add(new_memory)
    await db.commit()
    await db.refresh(new_memory)
    
    return MemoryResponse(
        id=new_memory.id,
        content=new_memory.content,
        metadata=new_memory.metadata or {},
        created_at=new_memory.created_at,
        tenant_id=new_memory.tenant_id
    )


@router.post(
    "/search",
    response_model=List[MemoryResponse],
    summary="Search memories",
    description="Search for similar memories using semantic search",
)
async def search_memories(
    request: MemorySearchRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> List[MemoryResponse]:
    """Search for similar memories."""
    logger.info(f"Searching memories with query: {request.query[:50]}...")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    # For now, do a simple text search
    # In production, this would use vector similarity search
    search_pattern = f"%{request.query}%"
    
    query = select(Memory).where(
        and_(
            Memory.tenant_id == auth.tenant_id,
            Memory.content.ilike(search_pattern)
        )
    ).limit(request.limit)
    
    result = await db.execute(query)
    memories = result.scalars().all()
    
    # Calculate mock similarity scores based on query match
    response_memories = []
    for memory in memories:
        # Simple similarity based on substring match
        similarity = 0.95 if request.query.lower() in memory.content.lower() else 0.80
        
        response_memories.append(
            MemoryResponse(
                id=memory.id,
                content=memory.content,
                metadata=memory.metadata or {},
                created_at=memory.created_at,
                similarity_score=similarity,
                tenant_id=memory.tenant_id
            )
        )
    
    # Sort by similarity score
    response_memories.sort(key=lambda x: x.similarity_score or 0, reverse=True)
    
    return response_memories


@router.get(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Get memory",
    description="Retrieve a specific memory by ID",
)
async def get_memory(
    memory_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> MemoryResponse:
    """Get memory by ID."""
    logger.info(f"Getting memory: {memory_id}")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    result = await db.execute(
        select(Memory).where(
            and_(
                Memory.tenant_id == auth.tenant_id,
                Memory.id == memory_id
            )
        )
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory not found: {memory_id}"
        )
    
    return MemoryResponse(
        id=memory.id,
        content=memory.content,
        metadata=memory.metadata or {},
        created_at=memory.created_at,
        tenant_id=memory.tenant_id
    )


@router.get(
    "/",
    response_model=List[MemoryResponse],
    summary="List memories",
    description="List all memories with pagination",
)
async def list_memories(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> List[MemoryResponse]:
    """List memories."""
    logger.info("Listing memories")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    query = select(Memory).where(
        Memory.tenant_id == auth.tenant_id
    ).order_by(Memory.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    memories = result.scalars().all()
    
    return [
        MemoryResponse(
            id=memory.id,
            content=memory.content,
            metadata=memory.metadata or {},
            created_at=memory.created_at,
            tenant_id=memory.tenant_id
        )
        for memory in memories
    ]


@router.put(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Update memory",
    description="Update an existing memory",
)
async def update_memory(
    memory_id: UUID,
    update: MemoryUpdate,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
) -> MemoryResponse:
    """Update a memory."""
    logger.info(f"Updating memory: {memory_id}")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    # Get existing memory
    result = await db.execute(
        select(Memory).where(
            and_(
                Memory.tenant_id == auth.tenant_id,
                Memory.id == memory_id
            )
        )
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory not found: {memory_id}"
        )
    
    # Update fields
    if update.content is not None:
        memory.content = update.content
    if update.metadata is not None:
        memory.metadata = update.metadata
    if update.embedding is not None:
        memory.embedding = update.embedding
    
    await db.commit()
    await db.refresh(memory)
    
    return MemoryResponse(
        id=memory.id,
        content=memory.content,
        metadata=memory.metadata or {},
        created_at=memory.created_at,
        tenant_id=memory.tenant_id
    )


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete memory",
    description="Delete a specific memory",
)
async def delete_memory(
    memory_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db)
):
    """Delete a memory."""
    logger.info(f"Deleting memory: {memory_id}")
    
    # Set tenant context for RLS
    await db.execute(f"SET LOCAL app.current_tenant_id = '{auth.tenant_id}'")
    
    # Get memory
    result = await db.execute(
        select(Memory).where(
            and_(
                Memory.tenant_id == auth.tenant_id,
                Memory.id == memory_id
            )
        )
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory not found: {memory_id}"
        )
    
    await db.delete(memory)
    await db.commit()
    
    return None