"""Unit tests for authentication system."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import jwt
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_api_key,
    generate_api_key,
    get_current_user,
    get_auth_context,
    AuthContext
)
from src.core.config import settings
from src.models.auth import User, Tenant, APIKey
from src.services.auth import AuthService


class TestJWTTokens:
    """Test JWT token generation and validation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = uuid4()
        tenant_id = uuid4()
        scopes = ["read", "write"]
        
        token = create_access_token(user_id, tenant_id, scopes)
        
        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["scopes"] == scopes
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        token = create_refresh_token(user_id, tenant_id)
        
        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_verify_valid_token(self):
        """Test verification of valid token."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        token = create_access_token(user_id, tenant_id)
        payload = verify_token(token)
        
        assert payload is not None
        assert payload.sub == str(user_id)
        assert payload.tenant_id == str(tenant_id)
        assert payload.type == "access"
    
    def test_verify_expired_token(self):
        """Test verification of expired token."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        # Create token with negative expiration
        with patch("src.core.auth.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() - timedelta(hours=1)
            token = create_access_token(user_id, tenant_id)
        
        payload = verify_token(token)
        assert payload is None
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        assert payload is None
    
    def test_verify_wrong_secret_token(self):
        """Test verification of token with wrong secret."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        # Create token with different secret
        token_payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "access",
            "exp": int((datetime.utcnow() + timedelta(minutes=30)).timestamp())
        }
        wrong_secret_token = jwt.encode(token_payload, "wrong-secret", algorithm=settings.JWT_ALGORITHM)
        
        payload = verify_token(wrong_secret_token)
        assert payload is None


class TestAPIKeys:
    """Test API key generation and validation."""
    
    def test_generate_api_key(self):
        """Test API key generation."""
        key = generate_api_key()
        
        assert key.startswith("omnex_")
        assert len(key) == 38  # "omnex_" (6) + 32 random chars
        assert all(c in "abcdefghijklmnopqrstuvwxyz0123456789" for c in key[6:])
    
    def test_hash_api_key(self):
        """Test API key hashing."""
        key = "omnex_test123456789"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        
        # Same key should produce same hash
        assert hash1 == hash2
        
        # Hash should be different from original
        assert hash1 != key
        
        # Different keys should produce different hashes
        different_key = "omnex_different123"
        different_hash = hash_api_key(different_key)
        assert different_hash != hash1


class TestAuthDependencies:
    """Test authentication dependencies."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_bearer_token(self):
        """Test getting current user with Bearer token."""
        user_id = uuid4()
        tenant_id = uuid4()
        token = create_access_token(user_id, tenant_id)
        
        # Mock cache and database
        mock_cache = AsyncMock()
        mock_cache.get_user.return_value = None
        
        mock_db = AsyncMock()
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            is_active=True
        )
        
        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        with patch("src.core.auth.cache", mock_cache):
            result = await get_current_user(
                token=f"Bearer {token}",
                db=mock_db
            )
        
        assert result == mock_user
        mock_cache.get_user.assert_called_once_with(str(user_id))
        mock_cache.cache_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_api_key(self):
        """Test getting current user with API key."""
        user_id = uuid4()
        tenant_id = uuid4()
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        # Mock cache
        mock_cache = AsyncMock()
        mock_cache.get_api_key.return_value = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "is_active": True,
            "scopes": ["read", "write"]
        }
        
        mock_db = AsyncMock()
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            is_active=True
        )
        
        # Mock query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        with patch("src.core.auth.cache", mock_cache):
            result = await get_current_user(
                token=api_key,
                db=mock_db
            )
        
        assert result == mock_user
        mock_cache.get_api_key.assert_called_once_with(key_hash)
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        mock_db = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                token="Bearer invalid_token",
                db=mock_db
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid authentication credentials"
    
    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self):
        """Test getting current user when user is inactive."""
        user_id = uuid4()
        tenant_id = uuid4()
        token = create_access_token(user_id, tenant_id)
        
        mock_cache = AsyncMock()
        mock_cache.get_user.return_value = None
        
        mock_db = AsyncMock()
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            is_active=False  # Inactive user
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        with patch("src.core.auth.cache", mock_cache):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(
                    token=f"Bearer {token}",
                    db=mock_db
                )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "User account is inactive"
    
    @pytest.mark.asyncio
    async def test_get_auth_context(self):
        """Test getting auth context."""
        user_id = uuid4()
        tenant_id = uuid4()
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            is_active=True
        )
        
        mock_request = MagicMock()
        mock_request.state.auth_scopes = ["read", "write"]
        
        context = await get_auth_context(
            current_user=mock_user,
            request=mock_request
        )
        
        assert isinstance(context, AuthContext)
        assert context.user_id == user_id
        assert context.tenant_id == tenant_id
        assert context.scopes == ["read", "write"]


class TestAuthService:
    """Test authentication service."""
    
    @pytest.mark.asyncio
    async def test_register_user(self):
        """Test user registration."""
        mock_db = AsyncMock()
        
        # Mock tenant query
        mock_tenant = Tenant(
            id=uuid4(),
            name="Default",
            slug="default"
        )
        mock_tenant_result = MagicMock()
        mock_tenant_result.scalar_one_or_none.return_value = mock_tenant
        
        # Mock user query (no existing user)
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = None
        
        # Configure mock to return different results for different queries
        mock_db.execute.side_effect = [mock_tenant_result, mock_user_result]
        
        # Mock commit and refresh
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        
        service = AuthService(mock_db)
        
        user = await service.register_user(
            email="newuser@example.com",
            password="securepassword123",
            full_name="New User"
        )
        
        assert user is not None
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called
    
    @pytest.mark.asyncio
    async def test_register_existing_user(self):
        """Test registering an existing user."""
        mock_db = AsyncMock()
        
        # Mock tenant query
        mock_tenant = Tenant(
            id=uuid4(),
            name="Default",
            slug="default"
        )
        mock_tenant_result = MagicMock()
        mock_tenant_result.scalar_one_or_none.return_value = mock_tenant
        
        # Mock user query (existing user)
        mock_existing_user = User(
            id=uuid4(),
            email="existing@example.com"
        )
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_existing_user
        
        mock_db.execute.side_effect = [mock_tenant_result, mock_user_result]
        
        service = AuthService(mock_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.register_user(
                email="existing@example.com",
                password="password123",
                full_name="Existing User"
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_authenticate_user_valid(self):
        """Test authenticating valid user."""
        mock_db = AsyncMock()
        
        # Create mock user with hashed password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        mock_user = User(
            id=uuid4(),
            tenant_id=uuid4(),
            email="test@example.com",
            password_hash=pwd_context.hash("correctpassword"),
            is_active=True
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        service = AuthService(mock_db)
        
        user = await service.authenticate_user(
            email="test@example.com",
            password="correctpassword"
        )
        
        assert user == mock_user
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Test authenticating user with wrong password."""
        mock_db = AsyncMock()
        
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        mock_user = User(
            id=uuid4(),
            tenant_id=uuid4(),
            email="test@example.com",
            password_hash=pwd_context.hash("correctpassword"),
            is_active=True
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        service = AuthService(mock_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate_user(
                email="test@example.com",
                password="wrongpassword"
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid email or password"
    
    @pytest.mark.asyncio
    async def test_create_api_key(self):
        """Test API key creation."""
        mock_db = AsyncMock()
        user_id = uuid4()
        tenant_id = uuid4()
        
        # Mock commit and refresh
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        
        # Mock cache
        mock_cache = AsyncMock()
        
        service = AuthService(mock_db)
        
        with patch("src.services.auth.cache", mock_cache):
            api_key, key_model = await service.create_api_key(
                user_id=user_id,
                tenant_id=tenant_id,
                name="Test API Key",
                scopes=["read", "write"]
            )
        
        assert api_key.startswith("omnex_")
        assert key_model is not None
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_cache.cache_api_key.called


class TestTenantIsolation:
    """Test tenant isolation mechanisms."""
    
    @pytest.mark.asyncio
    async def test_auth_context_tenant_isolation(self):
        """Test that auth context properly isolates tenants."""
        tenant1_id = uuid4()
        tenant2_id = uuid4()
        user1_id = uuid4()
        user2_id = uuid4()
        
        # Create two users in different tenants
        user1 = User(id=user1_id, tenant_id=tenant1_id, email="user1@tenant1.com")
        user2 = User(id=user2_id, tenant_id=tenant2_id, email="user2@tenant2.com")
        
        mock_request = MagicMock()
        mock_request.state.auth_scopes = []
        
        # Get auth contexts
        context1 = await get_auth_context(user1, mock_request)
        context2 = await get_auth_context(user2, mock_request)
        
        # Verify tenant isolation
        assert context1.tenant_id == tenant1_id
        assert context2.tenant_id == tenant2_id
        assert context1.tenant_id != context2.tenant_id
    
    def test_jwt_token_includes_tenant_id(self):
        """Test that JWT tokens include tenant ID."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        token = create_access_token(user_id, tenant_id)
        payload = verify_token(token)
        
        assert payload.tenant_id == str(tenant_id)
    
    @pytest.mark.asyncio
    async def test_api_key_tenant_validation(self):
        """Test that API keys are validated against correct tenant."""
        user_id = uuid4()
        tenant_id = uuid4()
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        
        # Mock cache with API key data
        mock_cache = AsyncMock()
        mock_cache.get_api_key.return_value = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "is_active": True,
            "scopes": ["read"]
        }
        
        # Mock user with matching tenant
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            is_active=True
        )
        
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        with patch("src.core.auth.cache", mock_cache):
            result = await get_current_user(token=api_key, db=mock_db)
        
        assert result.tenant_id == tenant_id


class TestAuthMiddleware:
    """Test authentication middleware behavior."""
    
    @pytest.mark.asyncio
    async def test_middleware_sets_auth_scopes(self):
        """Test that middleware properly sets auth scopes on request."""
        user_id = uuid4()
        tenant_id = uuid4()
        scopes = ["read", "write"]
        
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="test@example.com",
            is_active=True
        )
        
        mock_request = MagicMock()
        mock_request.state.auth_scopes = scopes
        
        context = await get_auth_context(mock_user, mock_request)
        
        assert context.scopes == scopes
    
    @pytest.mark.asyncio
    async def test_optional_auth_allows_no_token(self):
        """Test that optional auth allows requests without token."""
        from src.core.auth import get_optional_auth_context
        
        mock_db = AsyncMock()
        
        # Test with no authorization header
        context = await get_optional_auth_context(
            authorization=None,
            db=mock_db
        )
        
        assert context is None
    
    @pytest.mark.asyncio
    async def test_optional_auth_validates_token(self):
        """Test that optional auth still validates provided tokens."""
        from src.core.auth import get_optional_auth_context
        
        mock_db = AsyncMock()
        
        # Test with invalid token
        with pytest.raises(HTTPException) as exc_info:
            await get_optional_auth_context(
                authorization="Bearer invalid_token",
                db=mock_db
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED