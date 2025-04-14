"""
Conversation Module

This module provides functionality for managing conversations.
"""

from src.conversation.models import (
    Conversation,
    ConversationTurn,
    ConversationStatus,
    ConversationRole,
    ConversationSummary,
    PaginatedResult
)
from src.conversation.service import (
    ConversationService,
    create_conversation_service
)

__all__ = [
    'Conversation',
    'ConversationTurn',
    'ConversationStatus',
    'ConversationRole',
    'ConversationSummary',
    'PaginatedResult',
    'ConversationService',
    'create_conversation_service'
]