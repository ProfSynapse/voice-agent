"""
Tests for the conversation management service.

This module contains tests for the conversation management service functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from datetime import datetime

from src.conversation.service import ConversationService
from src.conversation.models import Conversation, ConversationTurn, TurnRole


class TestConversationService:
    """Test suite for the ConversationService class."""

    @pytest.fixture
    def mock_supabase_table(self):
        """Create a mock Supabase table utility."""
        mock_table = AsyncMock()
        mock_table.get_all.return_value = []
        mock_table.get_by_id.return_value = None
        mock_table.create.return_value = {}
        mock_table.update.return_value = {}
        mock_table.delete.return_value = True
        return mock_table

    @pytest.fixture
    def conversation_service(self, mock_supabase_client, mock_supabase_table):
        """Create a conversation service instance for testing."""
        with patch('src.utils.supabase_client.SupabaseTable', return_value=mock_supabase_table):
            service = ConversationService(mock_supabase_client)
            return service

    @pytest.mark.asyncio
    async def test_create_conversation(self, conversation_service, mock_supabase_table):
        """Test creating a new conversation."""
        # Arrange
        user_id = "test-user-id"
        title = "Test Conversation"
        system_prompt_id = "test-prompt-id"
        
        # Mock the create method to return a conversation
        mock_supabase_table.create.return_value = {
            "id": "test-conversation-id",
            "user_id": user_id,
            "title": title,
            "system_prompt_id": system_prompt_id,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "is_archived": False
        }
        
        # Act
        conversation = await conversation_service.create_conversation(
            user_id=user_id,
            title=title,
            system_prompt_id=system_prompt_id
        )
        
        # Assert
        assert conversation is not None
        assert conversation.id == "test-conversation-id"
        assert conversation.user_id == user_id
        assert conversation.title == title
        assert conversation.system_prompt_id == system_prompt_id
        assert conversation.is_archived is False
        
        # Verify Supabase table was called correctly
        mock_supabase_table.create.assert_called_once()
        create_args = mock_supabase_table.create.call_args[0][0]
        assert create_args["user_id"] == user_id
        assert create_args["title"] == title
        assert create_args["system_prompt_id"] == system_prompt_id

    @pytest.mark.asyncio
    async def test_get_conversation(self, conversation_service, mock_supabase_table):
        """Test getting a conversation by ID."""
        # Arrange
        conversation_id = "test-conversation-id"
        
        # Mock the get_by_id method to return a conversation
        mock_supabase_table.get_by_id.return_value = {
            "id": conversation_id,
            "user_id": "test-user-id",
            "title": "Test Conversation",
            "system_prompt_id": "test-prompt-id",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "is_archived": False
        }
        
        # Act
        conversation = await conversation_service.get_conversation(conversation_id)
        
        # Assert
        assert conversation is not None
        assert conversation.id == conversation_id
        assert conversation.user_id == "test-user-id"
        assert conversation.title == "Test Conversation"
        
        # Verify Supabase table was called correctly
        mock_supabase_table.get_by_id.assert_called_once_with(conversation_id)

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, conversation_service, mock_supabase_table):
        """Test getting a non-existent conversation."""
        # Arrange
        conversation_id = "non-existent-id"
        mock_supabase_table.get_by_id.return_value = None
        
        # Act
        conversation = await conversation_service.get_conversation(conversation_id)
        
        # Assert
        assert conversation is None
        mock_supabase_table.get_by_id.assert_called_once_with(conversation_id)

    @pytest.mark.asyncio
    async def test_get_user_conversations(self, conversation_service, mock_supabase_table):
        """Test getting all conversations for a user."""
        # Arrange
        user_id = "test-user-id"
        
        # Mock the get_all method to return conversations
        mock_supabase_table.get_all.return_value = [
            {
                "id": "conversation-1",
                "user_id": user_id,
                "title": "Conversation 1",
                "system_prompt_id": "prompt-1",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "is_archived": False
            },
            {
                "id": "conversation-2",
                "user_id": user_id,
                "title": "Conversation 2",
                "system_prompt_id": "prompt-2",
                "created_at": "2023-01-02T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z",
                "is_archived": True
            }
        ]
        
        # Act
        conversations = await conversation_service.get_user_conversations(user_id)
        
        # Assert
        assert len(conversations) == 2
        assert conversations[0].id == "conversation-1"
        assert conversations[0].title == "Conversation 1"
        assert conversations[0].is_archived is False
        assert conversations[1].id == "conversation-2"
        assert conversations[1].title == "Conversation 2"
        assert conversations[1].is_archived is True
        
        # Verify Supabase table was called correctly
        mock_supabase_table.get_all.assert_called_once()
        query_params = mock_supabase_table.get_all.call_args[0][0]
        assert query_params["filters"][0]["column"] == "user_id"
        assert query_params["filters"][0]["value"] == user_id

    @pytest.mark.asyncio
    async def test_update_conversation(self, conversation_service, mock_supabase_table):
        """Test updating a conversation."""
        # Arrange
        conversation_id = "test-conversation-id"
        new_title = "Updated Title"
        
        # Mock the update method to return the updated conversation
        mock_supabase_table.update.return_value = {
            "id": conversation_id,
            "user_id": "test-user-id",
            "title": new_title,
            "system_prompt_id": "test-prompt-id",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "is_archived": False
        }
        
        # Act
        updated = await conversation_service.update_conversation(
            conversation_id=conversation_id,
            title=new_title
        )
        
        # Assert
        assert updated is not None
        assert updated.id == conversation_id
        assert updated.title == new_title
        
        # Verify Supabase table was called correctly
        mock_supabase_table.update.assert_called_once()
        update_id = mock_supabase_table.update.call_args[0][0]
        update_data = mock_supabase_table.update.call_args[0][1]
        assert update_id == conversation_id
        assert update_data["title"] == new_title

    @pytest.mark.asyncio
    async def test_archive_conversation(self, conversation_service, mock_supabase_table):
        """Test archiving a conversation."""
        # Arrange
        conversation_id = "test-conversation-id"
        
        # Mock the update method to return the archived conversation
        mock_supabase_table.update.return_value = {
            "id": conversation_id,
            "user_id": "test-user-id",
            "title": "Test Conversation",
            "system_prompt_id": "test-prompt-id",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "is_archived": True
        }
        
        # Act
        success = await conversation_service.archive_conversation(conversation_id)
        
        # Assert
        assert success is True
        
        # Verify Supabase table was called correctly
        mock_supabase_table.update.assert_called_once()
        update_id = mock_supabase_table.update.call_args[0][0]
        update_data = mock_supabase_table.update.call_args[0][1]
        assert update_id == conversation_id
        assert update_data["is_archived"] is True

    @pytest.mark.asyncio
    async def test_delete_conversation(self, conversation_service, mock_supabase_table):
        """Test deleting a conversation."""
        # Arrange
        conversation_id = "test-conversation-id"
        mock_supabase_table.delete.return_value = True
        
        # Act
        success = await conversation_service.delete_conversation(conversation_id)
        
        # Assert
        assert success is True
        mock_supabase_table.delete.assert_called_once_with(conversation_id)

    @pytest.mark.asyncio
    async def test_add_conversation_turn(self, conversation_service, mock_supabase_table):
        """Test adding a turn to a conversation."""
        # Arrange
        conversation_id = "test-conversation-id"
        role = TurnRole.USER
        content = "Hello, how are you?"
        
        # Mock the create method to return a turn
        mock_supabase_table.create.return_value = {
            "id": "test-turn-id",
            "conversation_id": conversation_id,
            "role": role.value,
            "content": content,
            "audio_url": None,
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        # Act
        turn = await conversation_service.add_conversation_turn(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        
        # Assert
        assert turn is not None
        assert turn.id == "test-turn-id"
        assert turn.conversation_id == conversation_id
        assert turn.role == role
        assert turn.content == content
        
        # Verify Supabase table was called correctly
        mock_supabase_table.create.assert_called_once()
        create_args = mock_supabase_table.create.call_args[0][0]
        assert create_args["conversation_id"] == conversation_id
        assert create_args["role"] == role.value
        assert create_args["content"] == content

    @pytest.mark.asyncio
    async def test_get_conversation_turns(self, conversation_service, mock_supabase_table):
        """Test getting all turns for a conversation."""
        # Arrange
        conversation_id = "test-conversation-id"
        
        # Mock the get_all method to return turns
        mock_supabase_table.get_all.return_value = [
            {
                "id": "turn-1",
                "conversation_id": conversation_id,
                "role": "user",
                "content": "Hello, how are you?",
                "audio_url": None,
                "created_at": "2023-01-01T00:00:00Z"
            },
            {
                "id": "turn-2",
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": "I'm doing well, thank you!",
                "audio_url": "https://example.com/audio.wav",
                "created_at": "2023-01-01T00:00:01Z"
            }
        ]
        
        # Act
        turns = await conversation_service.get_conversation_turns(conversation_id)
        
        # Assert
        assert len(turns) == 2
        assert turns[0].id == "turn-1"
        assert turns[0].role == TurnRole.USER
        assert turns[0].content == "Hello, how are you?"
        assert turns[1].id == "turn-2"
        assert turns[1].role == TurnRole.ASSISTANT
        assert turns[1].content == "I'm doing well, thank you!"
        assert turns[1].audio_url == "https://example.com/audio.wav"
        
        # Verify Supabase table was called correctly
        mock_supabase_table.get_all.assert_called_once()
        query_params = mock_supabase_table.get_all.call_args[0][0]
        assert query_params["filters"][0]["column"] == "conversation_id"
        assert query_params["filters"][0]["value"] == conversation_id
        assert query_params["order"][0]["column"] == "created_at"
        assert query_params["order"][0]["ascending"] is True