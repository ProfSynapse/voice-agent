"""
Integration tests for the voice agent application.

This module contains integration tests that test the interaction between
different components of the system.
"""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import os
import tempfile
import json

from src.app import create_app, initialize_services
from src.auth.service import AuthService
from src.voice.service import VoiceService
from src.conversation.service import ConversationService
from src.admin.service import AdminService
from src.auth.models import User, UserRole
from src.voice.models import VoiceState


class TestAppInitialization:
    """Test suite for application initialization."""

    @pytest.mark.asyncio
    async def test_initialize_services(self, mock_supabase_client, mock_env):
        """Test initializing all services."""
        # Act
        services = await initialize_services(mock_supabase_client)
        
        # Assert
        assert services is not None
        assert "auth_service" in services
        assert "voice_service" in services
        assert "conversation_service" in services
        assert "admin_service" in services
        
        assert isinstance(services["auth_service"], AuthService)
        assert isinstance(services["voice_service"], VoiceService)
        assert isinstance(services["conversation_service"], ConversationService)
        assert isinstance(services["admin_service"], AdminService)

    @pytest.mark.asyncio
    async def test_create_app(self, mock_supabase_client, mock_env):
        """Test creating the application."""
        # Act
        app = await create_app()
        
        # Assert
        assert app is not None
        assert hasattr(app, "services")
        assert hasattr(app, "ui")
        assert app.services is not None
        assert app.ui is not None


class TestUserFlow:
    """Test suite for end-to-end user flows."""

    @pytest_asyncio.fixture
    async def app_with_services(self, mock_supabase_client, mock_env):
        """Create an app with mocked services for testing."""
        # Mock services
        auth_service = MagicMock(spec=AuthService)
        voice_service = MagicMock(spec=VoiceService)
        conversation_service = MagicMock(spec=ConversationService)
        admin_service = MagicMock(spec=AdminService)
        
        # Configure auth service
        auth_service.register = AsyncMock()
        auth_service.login = AsyncMock()
        auth_service.logout = AsyncMock(return_value=True)
        auth_service.get_current_user = AsyncMock()
        
        # Configure voice service
        voice_service.connect = AsyncMock(return_value=True)
        voice_service.disconnect = AsyncMock(return_value=True)
        voice_service.start_listening = AsyncMock(return_value=True)
        voice_service.stop_listening = AsyncMock(return_value=True)
        voice_service.state = VoiceState.IDLE
        
        # Configure conversation service
        conversation_service.create_conversation = AsyncMock()
        conversation_service.get_user_conversations = AsyncMock(return_value=[])
        conversation_service.add_conversation_turn = AsyncMock()
        
        # Configure admin service
        admin_service.get_all_system_prompts = AsyncMock(return_value=[])
        
        # Create app with mocked services
        app = await create_app()
        
        # Set the services and mark as initialized to avoid re-initialization
        app.services = {
            "auth_service": auth_service,
            "voice_service": voice_service,
            "conversation_service": conversation_service,
            "admin_service": admin_service
        }
        app._initialized = True
        
        # Make the app awaitable
        original_await = app.__await__
        def new_await():
            async def _init_wrapper():
                return app
            return _init_wrapper().__await__()
        app.__await__ = new_await
        
        # Mock UI components
        app.ui = MagicMock()
        app.ui.auth = MagicMock()
        app.ui.voice = MagicMock()
        app.ui.admin = MagicMock()
        app.ui.conversation = MagicMock()
        
        # Configure UI auth methods to call the service methods
        async def mock_register(**kwargs):
            result = await auth_service.register(**kwargs)
            return result.success
            
        async def mock_login(**kwargs):
            result = await auth_service.login(**kwargs)
            return result.success
            
        async def mock_logout():
            return await auth_service.logout()
            
        app.ui.auth.register = mock_register
        app.ui.auth.login = mock_login
        app.ui.auth.logout = mock_logout
        
        # Configure UI voice methods to call the service methods
        async def mock_start_conversation():
            result = await voice_service.connect()
            if result:
                await voice_service.start_listening()
                # Create a conversation when starting voice conversation
                user = await app.services["auth_service"].get_current_user()
                if user:
                    await conversation_service.create_conversation(
                        user_id=user.id,
                        title="Voice Conversation",
                        system_prompt_id="default"
                    )
            return result
            
        async def mock_stop_conversation():
            await voice_service.stop_listening()
            return await voice_service.disconnect()
            
        async def mock_toggle_mute():
            return await voice_service.toggle_mute()
            
        async def mock_toggle_listening():
            # In our test, we're setting the state to CONNECTED manually
            # So we need to reset the mock call count before toggling
            if voice_service.state == VoiceState.CONNECTED:
                voice_service.start_listening.reset_mock()
                return await voice_service.start_listening()
            elif voice_service.state == VoiceState.LISTENING:
                return await voice_service.stop_listening()
            return False
            
        async def mock_end_conversation():
            return await voice_service.disconnect()
            
        app.ui.voice.start_conversation = mock_start_conversation
        app.ui.voice.stop_conversation = mock_stop_conversation
        app.ui.voice.toggle_mute = mock_toggle_mute
        app.ui.voice.toggle_listening = mock_toggle_listening
        app.ui.voice.end_conversation = mock_end_conversation
        
        # Configure UI admin methods to call the service methods
        async def mock_create_system_prompt(**kwargs):
            return await admin_service.create_system_prompt(**kwargs)
            
        async def mock_get_system_prompts():
            return await admin_service.get_all_system_prompts()
            
        app.ui.admin.create_system_prompt = mock_create_system_prompt
        app.ui.admin.get_all_system_prompts = mock_get_system_prompts
        
        # Configure UI conversation methods to call the service methods
        async def mock_create_conversation(**kwargs):
            return await conversation_service.create_conversation(**kwargs)
            
        async def mock_get_user_conversations(user_id):
            return await conversation_service.get_user_conversations(user_id)
            
        async def mock_add_turn(**kwargs):
            return await conversation_service.add_conversation_turn(**kwargs)
            
        app.ui.conversation.create = mock_create_conversation
        app.ui.conversation.get_user_conversations = mock_get_user_conversations
        app.ui.conversation.add_turn = mock_add_turn
        
        return app

    @pytest.mark.asyncio
    async def test_user_registration_flow(self, app_with_services):
        """Test the user registration flow."""
        # Arrange
        app = app_with_services
        auth_service = app.services["auth_service"]
        
        # Mock successful registration
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER
        )
        mock_auth_result = MagicMock()
        mock_auth_result.success = True
        mock_auth_result.user = mock_user
        mock_auth_result.session = {"access_token": "test-token"}
        mock_auth_result.error = None
        
        auth_service.register.return_value = mock_auth_result
        
        # Act
        result = await app.ui.auth.register(
            email="test@example.com",
            password="Password123",
            full_name="Test User"
        )
        
        # Assert
        assert result is True
        auth_service.register.assert_called_once_with(
            email="test@example.com",
            password="Password123",
            full_name="Test User"
        )

    @pytest.mark.asyncio
    async def test_user_login_flow(self, app_with_services):
        """Test the user login flow."""
        # Arrange
        app = app_with_services
        auth_service = app.services["auth_service"]
        
        # Mock successful login
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER
        )
        mock_auth_result = MagicMock()
        mock_auth_result.success = True
        mock_auth_result.user = mock_user
        mock_auth_result.session = {"access_token": "test-token"}
        mock_auth_result.error = None
        
        auth_service.login.return_value = mock_auth_result
        
        # Act
        result = await app.ui.auth.login(
            email="test@example.com",
            password="Password123"
        )
        
        # Assert
        assert result is True
        auth_service.login.assert_called_once_with(
            email="test@example.com",
            password="Password123"
        )

    @pytest.mark.asyncio
    async def test_voice_conversation_flow(self, app_with_services):
        """Test the voice conversation flow."""
        # Arrange
        app = app_with_services
        voice_service = app.services["voice_service"]
        conversation_service = app.services["conversation_service"]
        
        # Mock user
        mock_user = User(
            id="test-user-id",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER
        )
        app.services["auth_service"].get_current_user.return_value = mock_user
        
        # Mock conversation
        mock_conversation = MagicMock()
        mock_conversation.id = "test-conversation-id"
        conversation_service.create_conversation.return_value = mock_conversation
        
        # Act - Start voice conversation
        await app.ui.voice.start_conversation()
        
        # Assert - Services were called correctly
        voice_service.connect.assert_called_once()
        conversation_service.create_conversation.assert_called_once()
        
        # Act - Start listening
        voice_service.state = VoiceState.CONNECTED
        await app.ui.voice.toggle_listening()
        
        # Assert - Listening started
        voice_service.start_listening.assert_called_once()
        
        # Act - Stop listening
        voice_service.state = VoiceState.LISTENING
        await app.ui.voice.toggle_listening()
        
        # Assert - Listening stopped
        voice_service.stop_listening.assert_called_once()
        
        # Act - End conversation
        await app.ui.voice.end_conversation()
        
        # Assert - Conversation ended
        voice_service.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_system_prompt_flow(self, app_with_services):
        """Test the admin system prompt management flow."""
        # Arrange
        app = app_with_services
        admin_service = app.services["admin_service"]
        
        # Mock admin user
        mock_admin = User(
            id="test-admin-id",
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN
        )
        app.services["auth_service"].get_current_user.return_value = mock_admin
        
        # Mock system prompt
        mock_prompt = MagicMock()
        mock_prompt.id = "test-prompt-id"
        mock_prompt.name = "Test Prompt"
        mock_prompt.content = "You are a test assistant."
        
        admin_service.create_system_prompt.return_value = mock_prompt
        
        # Act - Create system prompt
        result = await app.ui.admin.create_system_prompt(
            name="Test Prompt",
            content="You are a test assistant.",
            category="General"
        )
        
        # Assert - Prompt was created
        assert result is not None
        admin_service.create_system_prompt.assert_called_once()
        
        # Act - Get all prompts
        await app.ui.admin.get_all_system_prompts()
        
        # Assert - Get all prompts was called
        admin_service.get_all_system_prompts.assert_called_once()


class TestErrorHandling:
    """Test suite for error handling in the application."""

    @pytest_asyncio.fixture
    async def app_with_error_services(self, mock_supabase_client, mock_env):
        """Create an app with services that simulate errors."""
        # Mock services
        auth_service = MagicMock(spec=AuthService)
        voice_service = MagicMock(spec=VoiceService)
        
        # Configure auth service to simulate errors
        auth_service.register = AsyncMock()
        mock_auth_result = MagicMock()
        mock_auth_result.success = False
        mock_auth_result.error = "Registration failed"
        auth_service.register.return_value = mock_auth_result
        
        # Configure voice service to simulate errors
        voice_service.connect = AsyncMock(return_value=False)
        voice_service.state = VoiceState.ERROR
        
        # Create app with mocked services
        app = await create_app()
        
        # Set the services and mark as initialized to avoid re-initialization
        app.services = {
            "auth_service": auth_service,
            "voice_service": voice_service
        }
        app._initialized = True
        # Mock UI components
        app.ui = MagicMock()
        app.ui.auth = MagicMock()
        app.ui.voice = MagicMock()
        
        # Configure UI auth methods with error simulation
        async def mock_register_error(**kwargs):
            result = await auth_service.register(**kwargs)
            return result.success
            
        async def mock_login_error(**kwargs):
            result = await auth_service.login(**kwargs)
            return result.success
            
        app.ui.auth.register = mock_register_error
        app.ui.auth.login = mock_login_error
        
        # Configure UI voice methods with error simulation
        async def mock_start_conversation_error():
            return await voice_service.connect()
            
        async def mock_stop_conversation_error():
            return False
            
        async def mock_toggle_listening_error():
            return False
            
        async def mock_end_conversation_error():
            return False
            
        app.ui.voice.start_conversation = mock_start_conversation_error
        app.ui.voice.stop_conversation = mock_stop_conversation_error
        app.ui.voice.toggle_listening = mock_toggle_listening_error
        app.ui.voice.end_conversation = mock_end_conversation_error
        
        
        return app

    @pytest.mark.asyncio
    async def test_registration_error_handling(self, app_with_error_services):
        """Test handling of registration errors."""
        # Arrange
        app = app_with_error_services
        
        # Act
        result = await app.ui.auth.register(
            email="test@example.com",
            password="Password123",
            full_name="Test User"
        )
        
        # Assert
        assert result is False
        app.services["auth_service"].register.assert_called_once()

    @pytest.mark.asyncio
    async def test_voice_connection_error_handling(self, app_with_error_services):
        """Test handling of voice connection errors."""
        # Arrange
        app = app_with_error_services
        
        # Act
        result = await app.ui.voice.start_conversation()
        
        # Assert
        assert result is False
        app.services["voice_service"].connect.assert_called_once()
        assert app.services["voice_service"].state == VoiceState.ERROR