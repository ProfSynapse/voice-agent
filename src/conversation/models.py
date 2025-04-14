"""
Conversation Models Module

This module provides the data models for conversations.
"""

import datetime
import enum
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass


class ConversationRole(enum.Enum):
    """Roles in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(enum.Enum):
    """Status of a conversation."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    id: str
    conversation_id: str
    role: ConversationRole
    content: str
    audio_url: Optional[str]
    created_at: datetime.datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationTurn':
        """
        Create a ConversationTurn from a dictionary.
        
        Args:
            data: Dictionary containing turn data
            
        Returns:
            ConversationTurn instance
        """
        return cls(
            id=data["id"],
            conversation_id=data["conversation_id"],
            role=ConversationRole(data["role"]),
            content=data["content"],
            audio_url=data.get("audio_url"),
            created_at=datetime.datetime.fromisoformat(data["created_at"])
        )


@dataclass
class Conversation:
    """A conversation between a user and the assistant."""
    id: str
    user_id: str
    title: str
    system_prompt_id: Optional[str]
    status: ConversationStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    turns: List[ConversationTurn]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], turns: Optional[List[Dict[str, Any]]] = None) -> 'Conversation':
        """
        Create a Conversation from a dictionary.
        
        Args:
            data: Dictionary containing conversation data
            turns: Optional list of turn dictionaries
            
        Returns:
            Conversation instance
        """
        conversation_turns = []
        if turns:
            conversation_turns = [ConversationTurn.from_dict(turn) for turn in turns]
        
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            title=data["title"],
            system_prompt_id=data.get("system_prompt_id"),
            status=ConversationStatus(data["status"]),
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.datetime.fromisoformat(data["updated_at"]),
            turns=conversation_turns
        )


@dataclass
class PaginatedResult:
    """A paginated result of items."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_more: bool


@dataclass
class ConversationSummary:
    """A summary of a conversation."""
    id: str
    user_id: str
    title: str
    status: ConversationStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    turn_count: int
    last_message: Optional[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSummary':
        """
        Create a ConversationSummary from a dictionary.
        
        Args:
            data: Dictionary containing conversation summary data
            
        Returns:
            ConversationSummary instance
        """
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            title=data["title"],
            status=ConversationStatus(data["status"]),
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.datetime.fromisoformat(data["updated_at"]),
            turn_count=data["turn_count"],
            last_message=data.get("last_message")
        )