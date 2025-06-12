"""Base service class with tenant isolation."""

from typing import Optional, Type, TypeVar, Generic
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query

from src.core.logging import get_logger
from src.models.base import Base

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """Base service with tenant isolation support."""
    
    def __init__(
        self,
        db: AsyncSession,
        model: Type[ModelType],
        tenant_id: Optional[UUID] = None
    ):
        """Initialize base service.
        
        Args:
            db: Database session
            model: SQLAlchemy model class
            tenant_id: Tenant ID for multi-tenant queries
        """
        self.db = db
        self.model = model
        self.tenant_id = tenant_id
        
    async def set_tenant_context(self, tenant_id: UUID) -> None:
        """Set tenant context for RLS.
        
        This sets a PostgreSQL session variable that RLS policies use.
        """
        if tenant_id:
            await self.db.execute(
                f"SET LOCAL app.current_tenant_id = '{tenant_id}'"
            )
            logger.debug(f"Set tenant context: {tenant_id}")
            
    def apply_tenant_filter(self, query: Query) -> Query:
        """Apply tenant filter to query if model has tenant_id."""
        if self.tenant_id and hasattr(self.model, "tenant_id"):
            query = query.filter(self.model.tenant_id == self.tenant_id)
        return query
        
    async def get(self, id: UUID) -> Optional[ModelType]:
        """Get a single record by ID."""
        query = select(self.model).where(self.model.id == id)
        
        # Apply tenant filter if applicable
        if self.tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == self.tenant_id)
            
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
        
    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        # Add tenant_id if applicable
        if self.tenant_id and hasattr(self.model, "tenant_id"):
            kwargs["tenant_id"] = self.tenant_id
            
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
        
    async def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """Update a record."""
        instance = await self.get(id)
        if not instance:
            return None
            
        for key, value in kwargs.items():
            setattr(instance, key, value)
            
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
        
    async def delete(self, id: UUID) -> bool:
        """Delete a record."""
        instance = await self.get(id)
        if not instance:
            return False
            
        await self.db.delete(instance)
        await self.db.commit()
        return True