"""Authentication API endpoints."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    get_auth_context, get_optional_auth_context, AuthContext,
    decode_token
)
from src.core.cache import RedisCache, get_cache
from src.core.database import get_db
from src.core.logging import get_logger
from src.services.auth import AuthService

logger = get_logger(__name__)

router = APIRouter()


# Request/Response models

class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User response."""
    id: UUID
    email: str
    full_name: Optional[str]
    tenant_id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login_at: Optional[datetime]


class APIKeyCreate(BaseModel):
    """API key creation request."""
    name: str = Field(..., min_length=1, max_length=255)
    scopes: Optional[List[str]] = []
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key response."""
    id: UUID
    key: Optional[str] = None  # Only returned on creation
    prefix: str
    name: str
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]


# Endpoints

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """Register a new user."""
    auth_service = AuthService(db, cache)
    
    try:
        user = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            tenant_id=user.tenant_id,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """Login and receive access tokens."""
    auth_service = AuthService(db, cache)
    
    # Authenticate user
    user = await auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    # Create tokens
    tokens = await auth_service.create_tokens(user)
    
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """Refresh access token using refresh token."""
    auth_service = AuthService(db, cache)
    
    result = await auth_service.refresh_access_token(request.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
        
    return TokenResponse(**result)


@router.post("/logout")
async def logout(
    response: Response,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """Logout and invalidate tokens."""
    # For JWT, we can blacklist the token
    # Note: This requires the token to have a jti claim
    
    # Clear any auth cookies (if using cookies)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    # Invalidate user cache
    if cache and auth.user_id:
        await cache.invalidate_user(str(auth.user_id))
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """Get current user information."""
    if not auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with user account"
        )
        
    auth_service = AuthService(db, cache)
    user = await auth_service.get_user_by_id(auth.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    # Handle both User object and dict from cache
    if isinstance(user, dict):
        return UserResponse(**user)
    else:
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            tenant_id=user.tenant_id,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """Create a new API key."""
    if not auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication required"
        )
        
    auth_service = AuthService(db, cache)
    
    try:
        result = await auth_service.create_api_key(
            user_id=auth.user_id,
            name=key_data.name,
            scopes=key_data.scopes,
            expires_at=key_data.expires_at
        )
        
        return APIKeyResponse(
            id=UUID(result["id"]),
            key=result["key"],  # Only returned on creation!
            prefix=result["prefix"],
            name=result["name"],
            created_at=datetime.fromisoformat(result["created_at"]),
            last_used_at=None,
            expires_at=key_data.expires_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """List all API keys for the current user."""
    if not auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication required"
        )
        
    auth_service = AuthService(db, cache)
    keys = await auth_service.list_api_keys(auth.user_id)
    
    return [
        APIKeyResponse(
            id=UUID(key["id"]),
            prefix=key["prefix"],
            name=key["name"],
            created_at=datetime.fromisoformat(key["created_at"]),
            last_used_at=datetime.fromisoformat(key["last_used_at"]) if key["last_used_at"] else None,
            expires_at=datetime.fromisoformat(key["expires_at"]) if key["expires_at"] else None
        )
        for key in keys
    ]


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
):
    """Delete an API key."""
    if not auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication required"
        )
        
    auth_service = AuthService(db, cache)
    success = await auth_service.revoke_api_key(auth.user_id, key_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
        
    return {"message": "API key deleted successfully"}