"""Authentication dependencies and utilities."""

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union, List
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class AuthContext(BaseModel):
    """Authentication context for requests."""
    tenant_id: UUID
    user_id: Optional[UUID] = None
    api_key_id: Optional[UUID] = None
    auth_method: str  # "jwt" or "api_key"
    scopes: Optional[List[str]] = []
    is_superuser: bool = False


class TokenData(BaseModel):
    """JWT token payload data."""
    sub: str  # Subject (user_id)
    tenant_id: str
    exp: int  # Expiration
    iat: int  # Issued at
    jti: str  # JWT ID (for blacklisting)
    type: str  # "access" or "refresh"
    scopes: Optional[List[str]] = []


# Password utilities

def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


# API Key utilities

def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key.
    
    Returns:
        tuple: (full_key, key_hash, prefix)
    """
    # Generate 32 bytes of randomness
    key_bytes = secrets.token_bytes(32)
    full_key = f"omnex_{key_bytes.hex()}"
    
    # Create hash for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    # Extract prefix for display (first 10 chars after "omnex_")
    prefix = full_key[:15]
    
    return full_key, key_hash, prefix


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage/lookup."""
    return hashlib.sha256(api_key.encode()).hexdigest()


# JWT utilities

def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    scopes: Optional[List[str]] = None
) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = TokenData(
        sub=str(user_id),
        tenant_id=str(tenant_id),
        exp=int(expire.timestamp()),
        iat=int(now.timestamp()),
        jti=secrets.token_urlsafe(16),
        type="access",
        scopes=scopes or []
    )
    
    token = jwt.encode(
        payload.model_dump(),
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token


def create_refresh_token(
    user_id: UUID,
    tenant_id: UUID
) -> tuple[str, str, datetime]:
    """Create a JWT refresh token.
    
    Returns:
        tuple: (token, token_hash, expires_at)
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = TokenData(
        sub=str(user_id),
        tenant_id=str(tenant_id),
        exp=int(expire.timestamp()),
        iat=int(now.timestamp()),
        jti=secrets.token_urlsafe(16),
        type="refresh",
        scopes=[]
    )
    
    token = jwt.encode(
        payload.model_dump(),
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    # Hash for storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    return token, token_hash, expire


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return TokenData(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Dependency functions

async def get_auth_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract and validate bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def get_current_user_from_token(
    token: str = Depends(get_auth_token),
    cache: Optional[Any] = None  # RedisCache - will be injected later
) -> AuthContext:
    """Get current user from JWT token."""
    # Decode token
    token_data = decode_token(token)
    
    # Check if token is blacklisted
    if cache:
        is_blacklisted = await cache.is_token_blacklisted(token_data.jti)
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Create auth context
    return AuthContext(
        tenant_id=UUID(token_data.tenant_id),
        user_id=UUID(token_data.sub),
        auth_method="jwt",
        scopes=token_data.scopes,
        is_superuser=False  # Will be set from user data
    )


async def get_current_user_from_api_key(
    api_key: str,
    cache: Optional[Any] = None,  # RedisCache
    db: Optional[AsyncSession] = None
) -> AuthContext:
    """Get current user from API key."""
    from src.models.auth import APIKey
    
    # Hash the API key
    key_hash = hash_api_key(api_key)
    
    # Check cache first
    if cache:
        cached_data = await cache.get_cached_api_key(key_hash)
        if cached_data:
            return AuthContext(**cached_data)
    
    # Query database
    if not db:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    
    result = await db.execute(
        select(APIKey)
        .where(APIKey.key_hash == key_hash)
        .where(APIKey.is_active == True)
        .options(selectinload(APIKey.user))
    )
    api_key_obj = result.scalar_one_or_none()
    
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check expiration
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )
    
    # Update last used
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    
    # Create auth context
    auth_context = AuthContext(
        tenant_id=api_key_obj.tenant_id,
        user_id=api_key_obj.user_id,
        api_key_id=api_key_obj.id,
        auth_method="api_key",
        scopes=json.loads(api_key_obj.scopes) if api_key_obj.scopes else [],
        is_superuser=api_key_obj.user.is_superuser
    )
    
    # Cache the result
    if cache:
        await cache.cache_api_key(key_hash, auth_context.model_dump(mode="json"))
    
    return auth_context


async def get_auth_context(
    authorization: Optional[str] = Depends(get_auth_token),
    cache: Optional[Any] = None,  # RedisCache
    db: Optional[AsyncSession] = None
) -> AuthContext:
    """Get authentication context from either JWT or API key."""
    if not authorization:
        # Check if multi-tenant is disabled (self-hosted mode)
        if not settings.ENABLE_MULTI_TENANT:
            return AuthContext(
                tenant_id=UUID(settings.DEFAULT_TENANT_ID),
                auth_method="none",
                is_superuser=False
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if it's an API key (starts with "omnex_")
    if authorization.startswith("omnex_"):
        return await get_current_user_from_api_key(authorization, cache, db)
    
    # Otherwise, treat as JWT
    return await get_current_user_from_token(authorization, cache)


# Optional auth for endpoints that work with or without auth
async def get_optional_auth_context(
    authorization: Optional[str] = None,
    cache: Optional[Any] = None,  # RedisCache
    db: Optional[AsyncSession] = None
) -> Optional[AuthContext]:
    """Get optional authentication context."""
    if not authorization:
        return None
    
    try:
        return await get_auth_context(authorization, cache, db)
    except HTTPException:
        return None


