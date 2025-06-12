"""Authentication service."""

import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, generate_api_key, hash_api_key,
    decode_token
)
from src.core.cache import RedisCache
from src.core.config import settings
from src.core.logging import get_logger
from src.models.auth import User, APIKey, RefreshToken, Tenant
from src.services.base import BaseService

logger = get_logger(__name__)


class AuthService(BaseService[User]):
    """Authentication service for user management."""
    
    def __init__(self, db: AsyncSession, cache: Optional[RedisCache] = None):
        """Initialize auth service."""
        super().__init__(db, User)
        self.cache = cache
        
    async def register_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        tenant_id: Optional[UUID] = None
    ) -> User:
        """Register a new user."""
        # Use default tenant if not specified (self-hosted mode)
        if not tenant_id and not settings.ENABLE_MULTI_TENANT:
            tenant_id = UUID(settings.DEFAULT_TENANT_ID)
            
        # Check if user already exists
        result = await self.db.execute(
            select(User)
            .where(
                and_(
                    User.tenant_id == tenant_id,
                    User.email == email
                )
            )
        )
        if result.scalar_one_or_none():
            raise ValueError("User with this email already exists")
            
        # Create user
        user = User(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            is_active=True,
            is_superuser=False
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Registered new user: {user.email}")
        return user
        
    async def authenticate_user(
        self,
        email: str,
        password: str,
        tenant_id: Optional[UUID] = None
    ) -> Optional[User]:
        """Authenticate a user with email and password."""
        # Build query
        query = select(User).where(User.email == email)
        
        # Add tenant filter if multi-tenant is enabled
        if settings.ENABLE_MULTI_TENANT and tenant_id:
            query = query.where(User.tenant_id == tenant_id)
        elif not settings.ENABLE_MULTI_TENANT:
            # Default tenant for self-hosted
            query = query.where(User.tenant_id == UUID(settings.DEFAULT_TENANT_ID))
            
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
            
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {user.email}")
            return None
            
        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        return user
        
    async def create_tokens(
        self,
        user: User
    ) -> Dict[str, Any]:
        """Create access and refresh tokens for a user."""
        # Create access token
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            scopes=["read", "write"]  # TODO: Implement proper scopes
        )
        
        # Create refresh token
        refresh_token, token_hash, expires_at = create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id
        )
        
        # Store refresh token
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(refresh_token_obj)
        await self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        """Refresh an access token using a refresh token."""
        try:
            # Decode refresh token
            token_data = decode_token(refresh_token)
            
            if token_data.type != "refresh":
                logger.warning("Invalid token type for refresh")
                return None
                
            # Hash token to find in database
            token_hash = hash_api_key(refresh_token)  # Reuse same hash function
            
            # Find refresh token
            result = await self.db.execute(
                select(RefreshToken)
                .where(RefreshToken.token_hash == token_hash)
                .options(selectinload(RefreshToken.user))
            )
            refresh_token_obj = result.scalar_one_or_none()
            
            if not refresh_token_obj:
                logger.warning("Refresh token not found")
                return None
                
            # Check if expired
            if refresh_token_obj.expires_at < datetime.now(timezone.utc):
                logger.warning("Refresh token expired")
                # Delete expired token
                await self.db.delete(refresh_token_obj)
                await self.db.commit()
                return None
                
            # Get user
            user = refresh_token_obj.user
            if not user.is_active:
                logger.warning(f"Inactive user attempted token refresh: {user.email}")
                return None
                
            # Create new access token
            access_token = create_access_token(
                user_id=user.id,
                tenant_id=user.tenant_id,
                scopes=["read", "write"]
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
            
    async def revoke_refresh_token(
        self,
        refresh_token: str
    ) -> bool:
        """Revoke a refresh token."""
        try:
            # Hash token
            token_hash = hash_api_key(refresh_token)
            
            # Delete from database
            result = await self.db.execute(
                select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            )
            refresh_token_obj = result.scalar_one_or_none()
            
            if refresh_token_obj:
                await self.db.delete(refresh_token_obj)
                await self.db.commit()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            return False
            
    async def create_api_key(
        self,
        user_id: UUID,
        name: str,
        scopes: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a new API key for a user."""
        # Get user to verify they exist and get tenant_id
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
            
        # Generate API key
        full_key, key_hash, prefix = generate_api_key()
        
        # Create API key object
        api_key = APIKey(
            tenant_id=user.tenant_id,
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            scopes=json.dumps(scopes) if scopes else None,
            expires_at=expires_at,
            is_active=True
        )
        
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        
        logger.info(f"Created API key '{name}' for user {user_id}")
        
        return {
            "id": str(api_key.id),
            "key": full_key,  # Only returned once!
            "prefix": prefix,
            "name": name,
            "created_at": api_key.created_at.isoformat()
        }
        
    async def list_api_keys(
        self,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """List all API keys for a user."""
        result = await self.db.execute(
            select(APIKey)
            .where(
                and_(
                    APIKey.user_id == user_id,
                    APIKey.is_active == True
                )
            )
            .order_by(APIKey.created_at.desc())
        )
        api_keys = result.scalars().all()
        
        return [
            {
                "id": str(key.id),
                "prefix": key.prefix,
                "name": key.name,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "created_at": key.created_at.isoformat()
            }
            for key in api_keys
        ]
        
    async def revoke_api_key(
        self,
        user_id: UUID,
        key_id: UUID
    ) -> bool:
        """Revoke an API key."""
        result = await self.db.execute(
            select(APIKey)
            .where(
                and_(
                    APIKey.id == key_id,
                    APIKey.user_id == user_id
                )
            )
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            return False
            
        api_key.is_active = False
        await self.db.commit()
        
        # Invalidate cache
        if self.cache:
            await self.cache.invalidate_api_key(api_key.key_hash)
            
        logger.info(f"Revoked API key {key_id} for user {user_id}")
        return True
        
    async def get_user_by_id(
        self,
        user_id: UUID
    ) -> Optional[User]:
        """Get a user by ID."""
        # Check cache first
        if self.cache:
            cached_user = await self.cache.get_cached_user(str(user_id))
            if cached_user:
                # Note: Returns dict, not User object
                return cached_user
                
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.tenant))
        )
        user = result.scalar_one_or_none()
        
        # Cache the result
        if user and self.cache:
            user_data = {
                "id": str(user.id),
                "tenant_id": str(user.tenant_id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser
            }
            await self.cache.cache_user(str(user_id), user_data)
            
        return user