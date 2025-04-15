"""
Conversation Core Module

This module provides the core functionality for the conversation service.
"""

import logging
from typing import Optional

from loguru import logger

from src.conversation.crud import ConversationCRUDService
from src.conversation.turn import ConversationTurnService
from src.conversation.search import ConversationSearchService
from src.security.field_encryption import get_field_encryption
from src.security.api_security import get_api_security_manager
from src.security.token_validation import get_token_validator
from src.security.error_handling import get_secure_error_handler


class ConversationService:
    """Service for managing conversations."""
    
    def __init__(self, supabase_client, storage_service):
        """
        Initialize the conversation service.
        
        Args:
            supabase_client: Initialized Supabase client
            storage_service: Storage service for audio files
        """
        # Initialize security components
        self.field_encryption = get_field_encryption()
        self.api_security = get_api_security_manager()
        self.token_validator = get_token_validator()
        self.error_handler = get_secure_error_handler()
        
        # Initialize sub-services
        self.crud = ConversationCRUDService(supabase_client, self.field_encryption, self.error_handler)
        self.turn = ConversationTurnService(supabase_client, storage_service, self.field_encryption, self.error_handler)
        self.search = ConversationSearchService(supabase_client, self.field_encryption, self.error_handler)
        
        # Store references to dependencies
        self.supabase = supabase_client
        self.storage = storage_service
    
    # Delegate methods to appropriate sub-services
    
    async def create_conversation(self, user_id: str, title: str, system_prompt_id: Optional[str] = None):
        """Create a new conversation."""
        return await self.crud.create_conversation(user_id, title, system_prompt_id)
    
    async def get_conversation(self, conversation_id: str, user_id: Optional[str] = None):
        """Get a conversation by ID."""
        return await self.crud.get_conversation(conversation_id, user_id)
    
    async def list_conversations(self, user_id: str, status=None, page: int = 1, page_size: int = 10):
        """List conversations for a user with pagination."""
        return await self.crud.list_conversations(user_id, status, page, page_size)
    
    async def update_conversation(self, conversation_id: str, user_id: str, **kwargs):
        """Update a conversation."""
        return await self.crud.update_conversation(conversation_id, user_id, **kwargs)
    
    async def delete_conversation(self, conversation_id: str, user_id: str):
        """Delete a conversation (mark as deleted)."""
        return await self.crud.delete_conversation(conversation_id, user_id)
    
    async def add_turn(self, conversation_id: str, role, content: str, audio_data=None):
        """Add a turn to a conversation."""
        return await self.turn.add_turn(conversation_id, role, content, audio_data)
    
    async def get_turn(self, turn_id: str):
        """Get a conversation turn by ID."""
        return await self.turn.get_turn(turn_id)
    
    async def search_conversations(self, user_id: str, query: str, page: int = 1, page_size: int = 10):
        """Search conversations by content."""
        return await self.search.search_conversations(user_id, query, page, page_size)


def create_conversation_service(supabase_client, storage_service):
    """
    Create and initialize the conversation service.
    
    Args:
        supabase_client: Initialized Supabase client
        storage_service: Storage service for audio files
        
    Returns:
        Initialized ConversationService instance
    """
    return ConversationService(supabase_client, storage_service)