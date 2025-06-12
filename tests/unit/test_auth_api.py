"""Unit tests for authentication API endpoints."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.models.auth import User, APIKey
from src.services.auth import AuthService
from src.core.database import get_db
from src.api.v1.auth import TokenResponse, UserResponse, APIKeyResponse


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def override_db(mock_db):
    """Override database dependency."""
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.clear()


class TestRegistrationEndpoint:
    """Test user registration endpoint."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client, mock_db, override_db):
        """Test successful registration."""
        # Mock user creation
        mock_user = User(
            id=uuid4(),
            tenant_id=uuid4(),
            email="newuser@example.com",
            full_name="New User",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        with patch.object(AuthService, 'register_user', return_value=mock_user):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass123!",
                    "full_name": "New User"
                }
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "tenant_id" in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, mock_db, override_db):
        """Test registration with duplicate email."""
        from fastapi import HTTPException
        
        with patch.object(
            AuthService,
            'register_user',
            side_effect=HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        ):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "password": "Pass123!",
                    "full_name": "User"
                }
            )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client, override_db):
        """Test registration with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "Pass123!",
                "full_name": "User"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client, override_db):
        """Test registration with weak password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "weak",
                "full_name": "User"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLoginEndpoint:
    """Test user login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, mock_db, override_db):
        """Test successful login."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="user@example.com",
            full_name="Test User",
            is_active=True
        )
        
        mock_refresh_token = "refresh_token_string"
        
        with patch.object(AuthService, 'authenticate_user', return_value=mock_user):
            with patch.object(AuthService, 'create_refresh_token', return_value=mock_refresh_token):
                response = client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "user@example.com",
                        "password": "Password123!"
                    }
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, mock_db, override_db):
        """Test login with invalid credentials."""
        from fastapi import HTTPException
        
        with patch.object(
            AuthService,
            'authenticate_user',
            side_effect=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        ):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "user@example.com",
                    "password": "WrongPassword"
                }
            )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client, mock_db, override_db):
        """Test login with inactive user."""
        from fastapi import HTTPException
        
        with patch.object(
            AuthService,
            'authenticate_user',
            side_effect=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        ):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "inactive@example.com",
                    "password": "Password123!"
                }
            )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "inactive" in response.json()["detail"]


class TestTokenRefreshEndpoint:
    """Test token refresh endpoint."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, mock_db, override_db):
        """Test successful token refresh."""
        user_id = uuid4()
        tenant_id = uuid4()
        token_id = uuid4()
        
        from src.models.auth import RefreshToken
        mock_token = RefreshToken(
            id=token_id,
            user_id=user_id,
            token_hash="hash",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="user@example.com",
            is_active=True
        )
        
        with patch.object(AuthService, 'validate_refresh_token', return_value=mock_token):
            with patch.object(AuthService, 'get_user_by_id', return_value=mock_user):
                with patch.object(AuthService, 'create_refresh_token', return_value="new_refresh_token"):
                    response = client.post(
                        "/api/v1/auth/refresh",
                        json={"refresh_token": "valid_refresh_token"}
                    )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client, mock_db, override_db):
        """Test refresh with invalid token."""
        with patch.object(AuthService, 'validate_refresh_token', return_value=None):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid_token"}
            )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid refresh token" in response.json()["detail"]


class TestUserProfileEndpoint:
    """Test user profile endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_profile_success(self, client, mock_db, override_db):
        """Test getting user profile."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="user@example.com",
            full_name="Test User",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Mock auth dependency
        from src.core.auth import get_current_user
        with patch("src.api.v1.auth.get_current_user", return_value=mock_user):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid_token"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "user@example.com"
        assert data["full_name"] == "Test User"
        assert data["id"] == str(user_id)
    
    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client, override_db):
        """Test getting profile without auth."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAPIKeyEndpoints:
    """Test API key management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_api_key_success(self, client, mock_db, override_db):
        """Test creating API key."""
        user_id = uuid4()
        tenant_id = uuid4()
        key_id = uuid4()
        
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="user@example.com"
        )
        
        mock_api_key = APIKey(
            id=key_id,
            user_id=user_id,
            tenant_id=tenant_id,
            name="Test Key",
            scopes=["read", "write"],
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        with patch("src.api.v1.auth.get_current_user", return_value=mock_user):
            with patch.object(
                AuthService,
                'create_api_key',
                return_value=("omnex_test123456", mock_api_key)
            ):
                response = client.post(
                    "/api/v1/auth/api-keys",
                    headers={"Authorization": "Bearer valid_token"},
                    json={
                        "name": "Test Key",
                        "scopes": ["read", "write"],
                        "expires_in_days": 90
                    }
                )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["key"] == "omnex_test123456"
        assert data["name"] == "Test Key"
        assert data["scopes"] == ["read", "write"]
    
    @pytest.mark.asyncio
    async def test_list_api_keys(self, client, mock_db, override_db):
        """Test listing user's API keys."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="user@example.com"
        )
        
        mock_keys = [
            APIKey(
                id=uuid4(),
                user_id=user_id,
                tenant_id=tenant_id,
                name="Key 1",
                scopes=["read"],
                is_active=True,
                created_at=datetime.utcnow(),
                last_used_at=datetime.utcnow()
            ),
            APIKey(
                id=uuid4(),
                user_id=user_id,
                tenant_id=tenant_id,
                name="Key 2",
                scopes=["read", "write"],
                is_active=False,
                created_at=datetime.utcnow()
            )
        ]
        
        with patch("src.api.v1.auth.get_current_user", return_value=mock_user):
            with patch.object(AuthService, 'list_user_api_keys', return_value=mock_keys):
                response = client.get(
                    "/api/v1/auth/api-keys",
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Key 1"
        assert data[0]["is_active"] is True
        assert data[1]["name"] == "Key 2"
        assert data[1]["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_revoke_api_key(self, client, mock_db, override_db):
        """Test revoking API key."""
        user_id = uuid4()
        key_id = uuid4()
        
        mock_user = User(
            id=user_id,
            email="user@example.com"
        )
        
        with patch("src.api.v1.auth.get_current_user", return_value=mock_user):
            with patch.object(AuthService, 'revoke_api_key', return_value=None):
                response = client.delete(
                    f"/api/v1/auth/api-keys/{key_id}",
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    @pytest.mark.asyncio
    async def test_revoke_nonexistent_api_key(self, client, mock_db, override_db):
        """Test revoking non-existent API key."""
        user_id = uuid4()
        key_id = uuid4()
        
        mock_user = User(
            id=user_id,
            email="user@example.com"
        )
        
        from fastapi import HTTPException
        
        with patch("src.api.v1.auth.get_current_user", return_value=mock_user):
            with patch.object(
                AuthService,
                'revoke_api_key',
                side_effect=HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            ):
                response = client.delete(
                    f"/api/v1/auth/api-keys/{key_id}",
                    headers={"Authorization": "Bearer valid_token"}
                )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, client, mock_db, override_db):
        """Test complete registration -> login -> api access flow."""
        user_id = uuid4()
        tenant_id = uuid4()
        
        # Step 1: Register
        mock_user = User(
            id=user_id,
            tenant_id=tenant_id,
            email="newuser@example.com",
            full_name="New User",
            is_active=True
        )
        
        with patch.object(AuthService, 'register_user', return_value=mock_user):
            register_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "SecurePass123!",
                    "full_name": "New User"
                }
            )
        
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # Step 2: Login
        with patch.object(AuthService, 'authenticate_user', return_value=mock_user):
            with patch.object(AuthService, 'create_refresh_token', return_value="refresh_token"):
                login_response = client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "newuser@example.com",
                        "password": "SecurePass123!"
                    }
                )
        
        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        # Step 3: Access protected endpoint
        with patch("src.api.v1.auth.get_current_user", return_value=mock_user):
            profile_response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        
        assert profile_response.status_code == status.HTTP_200_OK
        profile_data = profile_response.json()
        assert profile_data["email"] == "newuser@example.com"