"""
Pytest configuration file with common fixtures.

This module contains fixtures that can be used across all test files.
"""

import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from typing import Dict, Any

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
    env_vars = {
        "SUPABASE_URL": "https://test-supabase-url.com",
        "SUPABASE_KEY": "test-supabase-key",
        "LIVEKIT_URL": "wss://test-livekit-url.com",
        "LIVEKIT_API_KEY": "test-livekit-api-key",
        "LIVEKIT_API_SECRET": "test-livekit-api-secret",
        "OPENAI_API_KEY": "test-openai-api-key",
        "ENVIRONMENT": "test"
    }
    
    with patch.dict(os.environ, env_vars):
        with patch('src.config.environment.Environment.load') as mock_load:
            mock_load.return_value = Environment(
                supabase_url="https://test-supabase-url.com",
                supabase_key="test-supabase-key",
                livekit_url="wss://test-livekit-url.com",
                livekit_api_key="test-livekit-api-key",
                livekit_api_secret="test-livekit-api-secret",
                openai_api_key="test-openai-api-key",
                environment="test"
            )
            yield env_vars


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client for testing."""
    mock_client = MagicMock()
    
    # Mock auth methods
    mock_client.auth = MagicMock()
    mock_client.auth.sign_up = AsyncMock()
    mock_client.auth.sign_in = AsyncMock()
    mock_client.auth.sign_out = AsyncMock(return_value=True)
    mock_client.auth.get_user = AsyncMock()
    mock_client.auth.get_session = AsyncMock()
    mock_client.auth.refresh_session = AsyncMock()
    
    # Mock table methods
    mock_client.table = MagicMock(return_value=MagicMock())
    
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
def mock_voice_service():
    """Create a mock voice service for testing."""
    mock_service = MagicMock()
    mock_service.state = VoiceState.IDLE
    mock_service.is_muted = False
    mock_service.connect = AsyncMock(return_value=True)
    mock_service.disconnect = AsyncMock(return_value=True)
    mock_service.start_listening = AsyncMock(return_value=True)
    mock_service.stop_listening = AsyncMock(return_value=True)
    mock_service.toggle_mute = AsyncMock(return_value=False)
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