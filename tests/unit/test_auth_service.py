"""Unit tests for authentication service layer."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.auth import User, Tenant, APIKey, RefreshToken
from src.services.auth import AuthService
from src.core.config import settings


class TestAuthServiceRegistration:
    """Test user registration functionality."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test successful user registration."""
        mock_db = AsyncMock()
        
        # Mock tenant
        mock_tenant = Tenant(
            id=uuid4(),
            name="Default",
            slug="default"
        )
        
        # Setup mock returns
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = mock_tenant
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None  # No existing user
        
        mock_db.execute.side_effect = [tenant_result, user_result]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        
        service = AuthService(mock_db)
        
        # Register user
        user = await service.register_user(
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User"
        )
        
        # Verify
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called
        
        # Verify the user object passed to add
        added_user = mock_db.add.call_args[0][0]
        assert added_user.email == "newuser@example.com"
        assert added_user.full_name == "New User"
        assert added_user.tenant_id == mock_tenant.id
        assert added_user.password_hash != "SecurePass123!"  # Should be hashed
    
    @pytest.mark.asyncio
    async def test_register_user_custom_tenant(self):
        """Test user registration with custom tenant."""
        mock_db = AsyncMock()
        tenant_id = uuid4()
        
        # Mock tenant
        mock_tenant = Tenant(
            id=tenant_id,
            name="Custom Tenant",
            slug="custom"
        )
        
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = mock_tenant
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [tenant_result, user_result]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        
        service = AuthService(mock_db)
        
        # Register with specific tenant
        user = await service.register_user(
            email="user@custom.com",
            password="Pass123!",
            full_name="Custom User",
            tenant_id=tenant_id
        )
        
        # Verify tenant assignment
        added_user = mock_db.add.call_args[0][0]
        assert added_user.tenant_id == tenant_id
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self):
        """Test registering with existing email."""
        mock_db = AsyncMock()
        
        # Mock existing user
        existing_user = User(
            id=uuid4(),
            email="existing@example.com",
            tenant_id=uuid4()
        )
        
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = Tenant(id=uuid4())
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = existing_user
        
        mock_db.execute.side_effect = [tenant_result, user_result]
        
        service = AuthService(mock_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.register_user(
                email="existing@example.com",
                password="Pass123!",
                full_name="Another User"
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_register_invalid_tenant(self):
        """Test registration with invalid tenant ID."""
        mock_db = AsyncMock()
        
        # No tenant found
        tenant_result = MagicMock()
        tenant_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.return_value = tenant_result
        
        service = AuthService(mock_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.register_user(
                email="user@example.com",
                password="Pass123!",
                full_name="User",
                tenant_id=uuid4()
            )
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Tenant not found" in exc_info.value.detail


class TestAuthServiceAuthentication:
    """Test user authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_authenticate_valid_credentials(self):
        """Test authentication with valid credentials."""
        mock_db = AsyncMock()
        
        # Create user with hashed password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        mock_user = User(
            id=uuid4(),
            tenant_id=uuid4(),
            email="user@example.com",
            password_hash=pwd_context.hash("CorrectPassword123"),
            is_active=True
        )
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = user_result
        
        service = AuthService(mock_db)
        
        # Authenticate
        user = await service.authenticate_user(
            email="user@example.com",
            password="CorrectPassword123"
        )
        
        assert user == mock_user
    
    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(self):
        """Test authentication with invalid password."""
        mock_db = AsyncMock()
        
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        mock_user = User(
            id=uuid4(),
            email="user@example.com",
            password_hash=pwd_context.hash("CorrectPassword"),
            is_active=True
        )
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = user_result
        
        service = AuthService(mock_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate_user(
                email="user@example.com",
                password="WrongPassword"
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid email or password"
    
    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self):
        """Test authentication with non-existent user."""
        mock_db = AsyncMock()
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = user_result
        
        service = AuthService(mock_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate_user(
                email="nonexistent@example.com",
                password="Password123"
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid email or password"
    
    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self):
        """Test authentication with inactive user."""
        mock_db = AsyncMock()
        
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        mock_user = User(
            id=uuid4(),
            email="user@example.com",
            password_hash=pwd_context.hash("Password123"),
            is_active=False  # Inactive
        )
        
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = user_result
        
        service = AuthService(mock_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate_user(
                email="user@example.com",
                password="Password123"
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "account is inactive" in exc_info.value.detail


class TestAuthServiceTokens:
    """Test token management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self):
        """Test refresh token creation."""
        mock_db = AsyncMock()
        user_id = uuid4()
        
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        
        service = AuthService(mock_db)
        
        token = await service.create_refresh_token(user_id)
        
        # Verify token was created
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # Verify token model
        token_model = mock_db.add.call_args[0][0]
        assert isinstance(token_model, RefreshToken)
        assert token_model.user_id == user_id
        assert token_model.expires_at > datetime.utcnow()
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_token(self):
        """Test refresh token revocation."""
        mock_db = AsyncMock()
        token_id = uuid4()
        user_id = uuid4()
        
        # Mock existing token
        mock_token = RefreshToken(
            id=token_id,
            user_id=user_id,
            token_hash="hash",
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_revoked=False
        )
        
        token_result = MagicMock()
        token_result.scalar_one_or_none.return_value = mock_token
        mock_db.execute.return_value = token_result
        mock_db.commit = AsyncMock()
        
        service = AuthService(mock_db)
        
        await service.revoke_refresh_token(str(token_id), user_id)
        
        # Verify token was revoked
        assert mock_token.is_revoked is True
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_validate_refresh_token_valid(self):
        """Test validation of valid refresh token."""
        mock_db = AsyncMock()
        token_id = uuid4()
        user_id = uuid4()
        token = f"{token_id}:secrettoken"
        
        # Mock token
        mock_token = RefreshToken(
            id=token_id,
            user_id=user_id,
            token_hash="will_be_mocked",
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_revoked=False
        )
        
        token_result = MagicMock()
        token_result.scalar_one_or_none.return_value = mock_token
        mock_db.execute.return_value = token_result
        
        service = AuthService(mock_db)
        
        # Mock hash verification
        with patch.object(service.pwd_context, 'verify', return_value=True):
            result = await service.validate_refresh_token(token)
        
        assert result == mock_token
    
    @pytest.mark.asyncio
    async def test_validate_refresh_token_expired(self):
        """Test validation of expired refresh token."""
        mock_db = AsyncMock()
        token_id = uuid4()
        token = f"{token_id}:secrettoken"
        
        # Mock expired token
        mock_token = RefreshToken(
            id=token_id,
            token_hash="hash",
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
            is_revoked=False
        )
        
        token_result = MagicMock()
        token_result.scalar_one_or_none.return_value = mock_token
        mock_db.execute.return_value = token_result
        
        service = AuthService(mock_db)
        
        result = await service.validate_refresh_token(token)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_refresh_token_revoked(self):
        """Test validation of revoked refresh token."""
        mock_db = AsyncMock()
        token_id = uuid4()
        token = f"{token_id}:secrettoken"
        
        # Mock revoked token
        mock_token = RefreshToken(
            id=token_id,
            token_hash="hash",
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_revoked=True  # Revoked
        )
        
        token_result = MagicMock()
        token_result.scalar_one_or_none.return_value = mock_token
        mock_db.execute.return_value = token_result
        
        service = AuthService(mock_db)
        
        result = await service.validate_refresh_token(token)
        assert result is None


class TestAuthServiceAPIKeys:
    """Test API key management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_api_key(self):
        """Test API key creation."""
        mock_db = AsyncMock()
        user_id = uuid4()
        tenant_id = uuid4()
        
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = MagicMock()
        
        # Mock cache
        mock_cache = AsyncMock()
        
        service = AuthService(mock_db)
        
        with patch("src.services.auth.cache", mock_cache):
            key, model = await service.create_api_key(
                user_id=user_id,
                tenant_id=tenant_id,
                name="Test Key",
                scopes=["read", "write"],
                expires_in_days=90
            )
        
        # Verify API key format
        assert key.startswith("omnex_")
        assert len(key) == 38
        
        # Verify model creation
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # Verify cache call
        assert mock_cache.cache_api_key.called
        
        # Check model properties
        added_model = mock_db.add.call_args[0][0]
        assert isinstance(added_model, APIKey)
        assert added_model.user_id == user_id
        assert added_model.tenant_id == tenant_id
        assert added_model.name == "Test Key"
        assert added_model.scopes == ["read", "write"]
    
    @pytest.mark.asyncio
    async def test_revoke_api_key(self):
        """Test API key revocation."""
        mock_db = AsyncMock()
        key_id = uuid4()
        user_id = uuid4()
        tenant_id = uuid4()
        
        # Mock existing key
        mock_key = APIKey(
            id=key_id,
            user_id=user_id,
            tenant_id=tenant_id,
            name="Test Key",
            key_hash="hash",
            is_active=True
        )
        
        key_result = MagicMock()
        key_result.scalar_one_or_none.return_value = mock_key
        mock_db.execute.return_value = key_result
        mock_db.commit = AsyncMock()
        
        # Mock cache
        mock_cache = AsyncMock()
        
        service = AuthService(mock_db)
        
        with patch("src.services.auth.cache", mock_cache):
            await service.revoke_api_key(key_id, user_id)
        
        # Verify key was deactivated
        assert mock_key.is_active is False
        assert mock_db.commit.called
        
        # Verify cache invalidation
        assert mock_cache.invalidate_api_key.called
    
    @pytest.mark.asyncio
    async def test_list_user_api_keys(self):
        """Test listing user's API keys."""
        mock_db = AsyncMock()
        user_id = uuid4()
        tenant_id = uuid4()
        
        # Mock API keys
        mock_keys = [
            APIKey(
                id=uuid4(),
                user_id=user_id,
                tenant_id=tenant_id,
                name="Key 1",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            APIKey(
                id=uuid4(),
                user_id=user_id,
                tenant_id=tenant_id,
                name="Key 2",
                is_active=False,
                created_at=datetime.utcnow()
            )
        ]
        
        keys_result = MagicMock()
        keys_result.scalars.return_value.all.return_value = mock_keys
        mock_db.execute.return_value = keys_result
        
        service = AuthService(mock_db)
        
        keys = await service.list_user_api_keys(user_id)
        
        assert len(keys) == 2
        assert keys[0].name == "Key 1"
        assert keys[0].is_active is True
        assert keys[1].name == "Key 2"
        assert keys[1].is_active is False
    
    @pytest.mark.asyncio
    async def test_revoke_api_key_wrong_user(self):
        """Test revoking API key by wrong user."""
        mock_db = AsyncMock()
        key_id = uuid4()
        owner_id = uuid4()
        wrong_user_id = uuid4()
        
        # Mock key owned by different user
        mock_key = APIKey(
            id=key_id,
            user_id=owner_id,
            name="Test Key",
            is_active=True
        )
        
        key_result = MagicMock()
        key_result.scalar_one_or_none.return_value = mock_key
        mock_db.execute.return_value = key_result
        
        service = AuthService(mock_db)
        
        with pytest.raises(HTTPException) as exc_info:
            await service.revoke_api_key(key_id, wrong_user_id)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "API key not found" in exc_info.value.detail