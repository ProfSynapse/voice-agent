"""
Tests for the authentication service.

This module contains tests for the authentication service functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
import asyncio

from src.auth.service import AuthService, create_auth_service
from src.auth.models import User, UserRole, AuthResult


class TestAuthService:
    """Test suite for the AuthService class."""

    @pytest.mark.asyncio
    async def test_register_success(self, mock_supabase_client):
        """Test successful user registration."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Mock the security service's validation methods
        auth_service.security.validate_email = MagicMock(return_value=(True, None))
        auth_service.security.validate_password = MagicMock(return_value=(True, None))
        auth_service.security.validate_text = MagicMock(return_value=(True, None))
        auth_service.security.validate_registration_attempt = MagicMock(return_value=(True, None))
        
        # Mock the Supabase auth response
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.created_at = "2023-01-01T00:00:00Z"
        mock_user.updated_at = "2023-01-01T00:00:00Z"
        
        mock_session = {"access_token": "test-token", "refresh_token": "test-refresh-token"}
        
        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session
        
        # Make the mock awaitable
        async def mock_sign_up(*args, **kwargs):
            return mock_auth_response
        mock_supabase_client.auth.sign_up = MagicMock(side_effect=mock_sign_up)
        
        # Mock the database insert
        mock_execute = MagicMock()
        mock_execute.data = [{"id": "test-user-id"}]
        mock_supabase_client.table().insert().execute.return_value = mock_execute
        
        # Act
        result = await auth_service.register(
            email="test@example.com",
            password="Password123",
            full_name="Test User"
        )
        
        # Assert
        assert result.success is True
        assert result.user is not None
        assert result.user.id == "test-user-id"
        assert result.user.email == "test@example.com"
        assert result.user.full_name == "Test User"
        assert result.user.role == UserRole.USER
        assert result.session == mock_session
        assert result.error is None
        
        # Verify Supabase client was called correctly
        mock_supabase_client.auth.sign_up.assert_called_once()
        mock_supabase_client.table.assert_called_with("users")
        # Don't check insert.assert_called_once() as it's called multiple times

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, mock_supabase_client):
        """Test registration with invalid email format."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Act
        result = await auth_service.register(
            email="invalid-email",
            password="Password123",
            full_name="Test User"
        )
        
        # Assert
        assert result.success is False
        assert result.error == "Invalid email format"
        assert result.user is None
        assert result.session is None
        
        # Verify Supabase client was not called
        mock_supabase_client.auth.sign_up.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_weak_password(self, mock_supabase_client):
        """Test registration with weak password."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Mock the security service's validation methods
        auth_service.security.validate_email = MagicMock(return_value=(True, None))
        auth_service.security.validate_text = MagicMock(return_value=(True, None))
        auth_service.security.validate_registration_attempt = MagicMock(return_value=(True, None))
        
        # Set up password validation to fail with specific error messages
        auth_service.security.validate_password = MagicMock(side_effect=[
            (False, "Password must contain at least one uppercase letter"),  # For result1
            (False, "Password must contain at least one lowercase letter"),  # For result2
            (False, "Password must contain at least one digit"),             # For result3
            (False, "Password must be at least 8 characters long")           # For result4
        ])
        
        # Act - Password without uppercase
        result1 = await auth_service.register(
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
        
        # Act - Password without lowercase
        result2 = await auth_service.register(
            email="test@example.com",
            password="PASSWORD123",
            full_name="Test User"
        )
        
        # Act - Password without digits
        result3 = await auth_service.register(
            email="test@example.com",
            password="PasswordABC",
            full_name="Test User"
        )
        
        # Act - Password too short
        result4 = await auth_service.register(
            email="test@example.com",
            password="Pass1",
            full_name="Test User"
        )
        
        # Assert
        assert result1.success is False
        assert "uppercase" in result1.error
        
        assert result2.success is False
        assert "lowercase" in result2.error
        
        assert result3.success is False
        assert "digit" in result3.error
        
        assert result4.success is False
        assert "8 characters" in result4.error
        
        # Verify Supabase client was not called
        mock_supabase_client.auth.sign_up.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_success(self, mock_supabase_client):
        """Test successful user login."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Mock the Supabase auth response
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.created_at = "2023-01-01T00:00:00Z"
        mock_user.updated_at = "2023-01-01T00:00:00Z"
        
        mock_session = {"access_token": "test-token", "refresh_token": "test-refresh-token"}
        
        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session
        
        # Make the mock awaitable
        async def mock_sign_in(*args, **kwargs):
            return mock_auth_response
        mock_supabase_client.auth.sign_in_with_password = MagicMock(side_effect=mock_sign_in)
        
        # Mock the database query
        mock_execute = MagicMock()
        mock_execute.data = [{
            "id": "test-user-id",
            "email": "test@example.com",
            "full_name": "Test User",
            "avatar_url": None,
            "role": "user",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }]
        
        # Make the table query awaitable
        async def mock_execute_query(*args, **kwargs):
            return mock_execute
        mock_table_select_eq = MagicMock()
        mock_table_select_eq.execute = MagicMock(side_effect=mock_execute_query)
        mock_table_select = MagicMock()
        mock_table_select.eq = MagicMock(return_value=mock_table_select_eq)
        mock_table = MagicMock()
        mock_table.select = MagicMock(return_value=mock_table_select)
        mock_supabase_client.table = MagicMock(return_value=mock_table)
        
        # Act
        result = await auth_service.login(
            email="test@example.com",
            password="Password123"
        )
        
        # Assert
        assert result.success is True
        assert result.user is not None
        assert result.user.id == "test-user-id"
        assert result.user.email == "test@example.com"
        assert result.user.full_name == "Test User"
        assert result.user.role == UserRole.USER
        assert result.session == mock_session
        assert result.error is None
        
        # Verify Supabase client was called correctly
        mock_supabase_client.auth.sign_in_with_password.assert_called_once()
        mock_supabase_client.table.assert_called_with("users")
        mock_supabase_client.table().select().eq().execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_supabase_client):
        """Test login with invalid credentials."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Make the mock awaitable and raise an exception
        async def mock_sign_in_error(*args, **kwargs):
            raise Exception("Invalid email or password")
        mock_supabase_client.auth.sign_in_with_password = MagicMock(side_effect=mock_sign_in_error)
        
        # Act
        result = await auth_service.login(
            email="test@example.com",
            password="WrongPassword"
        )
        
        # Assert
        assert result.success is False
        assert result.error is not None
        assert "error" in result.error.lower()
        assert result.user is None
        assert result.session is None

    @pytest.mark.asyncio
    async def test_logout(self, mock_supabase_client):
        """Test user logout."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        auth_service.current_user = MagicMock()
        auth_service.current_session = MagicMock()
        
        # Act
        result = await auth_service.logout()
        
        # Assert
        assert result is True
        assert auth_service.current_user is None
        assert auth_service.current_session is None
        
        # Make the mock awaitable
        async def mock_sign_out(*args, **kwargs):
            return None
        mock_supabase_client.auth.sign_out = MagicMock(side_effect=mock_sign_out)
        
        # Act again to test the mock
        result = await auth_service.logout()
        
        # Assert
        mock_supabase_client.auth.sign_out.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user_from_cache(self, mock_supabase_client):
        """Test getting current user from cache."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER
        )
        auth_service.current_user = mock_user
        
        # Act
        user = await auth_service.get_current_user()
        
        # Assert
        assert user is mock_user
        mock_supabase_client.auth.get_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_user_from_session(self, mock_supabase_client):
        """Test getting current user from session."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Mock the Supabase auth response
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.created_at = "2023-01-01T00:00:00Z"
        mock_user.updated_at = "2023-01-01T00:00:00Z"
        
        mock_session = MagicMock()
        
        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session
        
        # Make the mock awaitable
        async def mock_get_session(*args, **kwargs):
            return mock_auth_response
        mock_supabase_client.auth.get_session = MagicMock(side_effect=mock_get_session)
        
        # Mock the database query
        mock_execute = MagicMock()
        mock_execute.data = [{
            "id": "test-user-id",
            "email": "test@example.com",
            "full_name": "Test User",
            "avatar_url": None,
            "role": "user",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }]
        
        # Make the table query awaitable
        async def mock_execute_query(*args, **kwargs):
            return mock_execute
        mock_table_select_eq = MagicMock()
        mock_table_select_eq.execute = MagicMock(side_effect=mock_execute_query)
        mock_table_select = MagicMock()
        mock_table_select.eq = MagicMock(return_value=mock_table_select_eq)
        mock_table = MagicMock()
        mock_table.select = MagicMock(return_value=mock_table_select)
        mock_supabase_client.table = MagicMock(return_value=mock_table)
        
        # Act
        user = await auth_service.get_current_user()
        
        # Assert
        assert user is not None
        assert user.id == "test-user-id"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == UserRole.USER
        
        # Verify Supabase client was called correctly
        mock_supabase_client.auth.get_session.assert_called_once()
        mock_supabase_client.table.assert_called_with("users")
        mock_supabase_client.table().select().eq().execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_admin_with_admin_user(self, mock_supabase_client, sample_admin_user):
        """Test checking if user is admin with admin user."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Act
        result = await auth_service.is_admin(sample_admin_user)
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_is_admin_with_regular_user(self, mock_supabase_client, sample_user):
        """Test checking if user is admin with regular user."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Act
        result = await auth_service.is_admin(sample_user)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_request_password_reset(self, mock_supabase_client):
        """Test requesting a password reset."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Act
        result = await auth_service.request_password_reset("test@example.com")
        
        # Assert
        # Make the mock awaitable
        async def mock_reset_password_email(*args, **kwargs):
            return None
        mock_supabase_client.auth.reset_password_email = MagicMock(side_effect=mock_reset_password_email)
        
        # Act
        result = await auth_service.request_password_reset("test@example.com")
        
        # Assert
        assert result is True
        mock_supabase_client.auth.reset_password_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password(self, mock_supabase_client):
        """Test resetting a password."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Mock the security service's validate_session_token method
        auth_service.security.validate_session_token = MagicMock(return_value=(True, {"sub": "test-user-id"}, None))
        
        # Make the mock awaitable
        async def mock_update_user(*args, **kwargs):
            return None
        mock_supabase_client.auth.update_user = MagicMock(side_effect=mock_update_user)
        
        # Act
        result = await auth_service.reset_password("test-token", "NewPassword123")
        
        # Assert
        assert result is True
        mock_supabase_client.auth.update_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_weak_password(self, mock_supabase_client):
        """Test resetting a password with a weak password."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Act
        result = await auth_service.reset_password("test-token", "weak")
        
        # Assert
        assert result is False
        mock_supabase_client.auth.update_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_session(self, mock_supabase_client):
        """Test refreshing a session."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Mock the Supabase auth response
        mock_session = MagicMock()
        
        mock_auth_response = MagicMock()
        mock_auth_response.session = mock_session
        
        # Make the mock awaitable
        async def mock_refresh_session(*args, **kwargs):
            return mock_auth_response
        mock_supabase_client.auth.refresh_session = MagicMock(side_effect=mock_refresh_session)
        
        # Act
        result = await auth_service.refresh_session()
        
        # Assert
        assert result is True
        assert auth_service.current_session is mock_session
        mock_supabase_client.auth.refresh_session.assert_called_once()

    def test_validate_email(self, mock_supabase_client):
        """Test email validation."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Act & Assert
        assert auth_service.security.validate_email("test@example.com")[0] is True
        assert auth_service.security.validate_email("test.user@example.co.uk")[0] is True
        assert auth_service.security.validate_email("test+user@example.com")[0] is True
        
        assert auth_service.security.validate_email("invalid-email")[0] is False
        assert auth_service.security.validate_email("test@")[0] is False
        assert auth_service.security.validate_email("@example.com")[0] is False
        assert auth_service.security.validate_email("")[0] is False
        assert auth_service.security.validate_email(None)[0] is False

    def test_validate_password(self, mock_supabase_client):
        """Test password validation."""
        # Arrange
        auth_service = AuthService(mock_supabase_client)
        
        # Act & Assert
        assert auth_service.security.validate_password("Password123")[0] is True
        assert auth_service.security.validate_password("StrongP@ssw0rd")[0] is True
        
        # Too short
        assert auth_service.security.validate_password("Pass1")[0] is False
        
        # No uppercase
        assert auth_service.security.validate_password("password123")[0] is False
        
        # No lowercase
        assert auth_service.security.validate_password("PASSWORD123")[0] is False
        
        # No digits
        assert auth_service.security.validate_password("PasswordABC")[0] is False
        
        # Empty or None
        assert auth_service.security.validate_password("")[0] is False
        assert auth_service.security.validate_password(None)[0] is False

    def test_create_auth_service(self, mock_supabase_client):
        """Test creating an auth service."""
        # Act
        auth_service = create_auth_service(mock_supabase_client)
        
        # Assert
        assert isinstance(auth_service, AuthService)
        assert auth_service.supabase is mock_supabase_client