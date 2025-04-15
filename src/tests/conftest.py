"""
Pytest configuration file with common fixtures.

This module contains fixtures that can be used across all test files.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from typing import Dict, Any

# Add mock_modules directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mock_modules'))

# Patch webrtcvad module before any imports that might use it
import webrtcvad
sys.modules['webrtcvad'] = webrtcvad

# Patch LiveKit modules before any imports that might use them
# Import mock modules
import livekit.plugins
import livekit.agents
import livekit.plugins.turn_detector.multilingual

# Add them to sys.modules
sys.modules['livekit.plugins'] = livekit.plugins
sys.modules['livekit.agents'] = livekit.agents
sys.modules['livekit.plugins.turn_detector.multilingual'] = livekit.plugins.turn_detector.multilingual

from src.auth.models import User, UserRole
from src.voice.models import VoiceState
from src.config.environment import Environment


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env():
    """Mock environment variables for testing."""
    # Use properly formatted JWT tokens for Supabase keys
    # Format: header.payload.signature
    env_vars = {
        "SUPABASE_URL": "https://test-supabase-url.com",
        "SUPABASE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgS2V5IiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkFub24gS2V5IiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "SUPABASE_SERVICE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlNlcnZpY2UgS2V5IiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "LIVEKIT_URL": "wss://test-livekit-url.com",
        "LIVEKIT_API_KEY": "test-livekit-api-key",
        "LIVEKIT_API_SECRET": "test-livekit-api-secret",
        "OPENAI_API_KEY": "test-openai-api-key",
        "ENVIRONMENT": "test"
    }
    
    # Create an environment instance and load our test variables
    env = Environment()
    
    # Patch os.environ to use our test variables
    with patch.dict(os.environ, env_vars):
        # Load the environment variables into the Environment instance
        env.load(env_vars)
        yield env_vars


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client for testing."""
    mock_client = MagicMock()
    
    # Mock auth methods
    mock_client.auth = MagicMock()
    mock_client.auth.sign_up = AsyncMock()
    mock_client.auth.sign_in = AsyncMock()
    mock_client.auth.sign_in_with_password = AsyncMock()
    mock_client.auth.sign_out = AsyncMock(return_value=True)
    mock_client.auth.get_user = AsyncMock()
    mock_client.auth.get_session = AsyncMock()
    mock_client.auth.refresh_session = AsyncMock()
    mock_client.auth.reset_password_email = AsyncMock()
    mock_client.auth.update_user = AsyncMock()
    
    # Create a mock user and session for auth responses
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"
    mock_user.created_at = "2023-01-01T00:00:00"
    mock_user.updated_at = "2023-01-01T00:00:00"
    
    mock_session = MagicMock()
    mock_session.access_token = "test-access-token"
    
    # Set up auth response
    auth_response = MagicMock()
    auth_response.user = mock_user
    auth_response.session = mock_session
    
    # Configure auth methods to return the mock response
    mock_client.auth.sign_in_with_password.return_value = auth_response
    mock_client.auth.sign_up.return_value = auth_response
    mock_client.auth.get_session.return_value = auth_response
    mock_client.auth.refresh_session.return_value = auth_response
    
    # Mock table methods with proper chaining for async operations
    # Create mock for table().select().eq().execute()
    mock_execute = AsyncMock()
    mock_execute.return_value.data = [{
        "id": "test-user-id",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }]
    
    mock_eq = MagicMock()
    mock_eq.execute = mock_execute
    mock_eq.single = MagicMock(return_value=mock_eq)
    
    mock_select = MagicMock()
    mock_select.eq = MagicMock(return_value=mock_eq)
    mock_select.order = MagicMock(return_value=mock_select)
    mock_select.range = MagicMock(return_value=mock_select)
    
    mock_table = MagicMock()
    mock_table.select = MagicMock(return_value=mock_select)
    
    # Mock insert operation
    mock_insert_execute = AsyncMock()
    mock_insert_execute.return_value.data = [{
        "id": "test-id",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }]
    
    mock_insert = MagicMock()
    mock_insert.execute = mock_insert_execute
    
    mock_table.insert = MagicMock(return_value=mock_insert)
    mock_table.update = MagicMock(return_value=mock_insert)  # Reuse the same pattern for update
    
    mock_client.table = MagicMock(return_value=mock_table)
    
    return mock_client


@pytest.fixture
def mock_supabase_table():
    """Create a mock Supabase table utility."""
    mock_table = AsyncMock()
    mock_table.get_all = AsyncMock(return_value=[])
    mock_table.get_by_id = AsyncMock(return_value=None)
    mock_table.create = AsyncMock(return_value={})
    mock_table.update = AsyncMock(return_value={})
    mock_table.delete = AsyncMock(return_value=True)
    return mock_table


@pytest.fixture
def mock_livekit_client():
    """Create a mock LiveKit client for testing."""
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.disconnect = AsyncMock(return_value=True)
    mock_client.create_local_tracks = AsyncMock(return_value=[])
    mock_client.publish_tracks = AsyncMock(return_value=True)
    mock_client.unpublish_tracks = AsyncMock(return_value=True)
    mock_client.mute_track = AsyncMock(return_value=True)
    mock_client.unmute_track = AsyncMock(return_value=True)
    
    return mock_client


@pytest.fixture
def regular_user():
    """Create a sample regular user for testing."""
    return User(
        id="test-user-id",
        email="user@example.com",
        full_name="Test User",
        role=UserRole.USER,
        avatar_url=None,
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z"
    )


@pytest.fixture
def admin_user():
    """Create a sample admin user for testing."""
    return User(
        id="test-admin-id",
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.ADMIN,
        avatar_url=None,
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z"
    )
@pytest.fixture
def sample_user():
    """Create a sample regular user for testing."""
    return User(
        id="test-user-id",
        email="user@example.com",
        full_name="Test User",
        role=UserRole.USER,
        avatar_url=None,
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z"
    )


@pytest.fixture
def sample_admin_user():
    """Create a sample admin user for testing."""
    return User(
        id="test-admin-id",
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.ADMIN,
        avatar_url=None,
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z"
    )


@pytest.fixture
def mock_voice_service():
    """Create a mock voice service for testing."""
    mock_service = MagicMock()
    mock_service.state = VoiceState.IDLE
    mock_service.is_muted = False
    
    # Mock basic voice service methods
    mock_service.connect = AsyncMock(return_value=True)
    mock_service.disconnect = AsyncMock(return_value=True)
    mock_service.start_listening = AsyncMock(return_value=True)
    mock_service.stop_listening = AsyncMock(return_value=True)
    mock_service.toggle_mute = AsyncMock(return_value=False)
    
    # Mock event handlers
    mock_service.set_on_speech_ended = MagicMock()
    mock_service.set_on_transcription = MagicMock()
    mock_service.set_on_error = MagicMock()
    mock_service.set_on_state_change = MagicMock()
    
    # Mock audio processing methods
    from datetime import datetime
    from src.voice.models import TranscriptionResult
    
    # Create a mock transcription result
    mock_transcription = TranscriptionResult(
        text="Hello, this is a test transcription",
        confidence=0.95,
        is_final=True,
        timestamp=datetime.now(),
        language="en-US"
    )
    
    # Mock the transcribe_audio method
    mock_service.transcribe_audio = AsyncMock(return_value=mock_transcription)
    
    # Mock the synthesize_speech method
    mock_service.synthesize_speech = AsyncMock(return_value=b"mock synthesized audio")
    
    # Mock the play_audio method - this is a MagicMock, not a function
    mock_service.play_audio = AsyncMock(return_value=True)
    
    return mock_service


@pytest.fixture
def mock_conversation_service():
    """Create a mock conversation service for testing."""
    mock_service = MagicMock()
    mock_service.create_conversation = AsyncMock()
    mock_service.get_conversation = AsyncMock()
    mock_service.get_user_conversations = AsyncMock(return_value=[])
    mock_service.add_conversation_turn = AsyncMock()
    mock_service.update_conversation = AsyncMock()
    mock_service.delete_conversation = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture
def sample_conversation_data():
    """Create sample conversation data for testing."""
    return {
        "id": "test-conversation-id",
        "user_id": "test-user-id",
        "title": "Test Conversation",
        "system_prompt_id": "test-prompt-id",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "turns": [
            {
                "id": "turn-1",
                "conversation_id": "test-conversation-id",
                "role": "user",
                "content": "Hello, how are you?",
                "created_at": "2023-01-01T00:00:01Z"
            },
            {
                "id": "turn-2",
                "conversation_id": "test-conversation-id",
                "role": "assistant",
                "content": "I'm doing well, thank you for asking!",
                "created_at": "2023-01-01T00:00:02Z"
            }
        ]
    }