"""
Admin Models Module

This module provides the data models for admin functionality.
"""

import datetime
import enum
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass


class PromptCategory(enum.Enum):
    """Categories for system prompts."""
    GENERAL = "general"
    CUSTOMER_SERVICE = "customer_service"
    TECHNICAL_SUPPORT = "technical_support"
    SALES = "sales"
    CUSTOM = "custom"


class UserStatus(enum.Enum):
    """Status of a user account."""
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING = "pending"


class MetricsPeriod(enum.Enum):
    """Time periods for metrics."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"


@dataclass
class SystemPrompt:
    """A system prompt for conversations."""
    id: str
    created_by: str
    name: str
    content: str
    category: PromptCategory
    is_default: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemPrompt':
        """
        Create a SystemPrompt from a dictionary.
        
        Args:
            data: Dictionary containing prompt data
            
        Returns:
            SystemPrompt instance
        """
        return cls(
            id=data["id"],
            created_by=data["created_by"],
            name=data["name"],
            content=data["content"],
            category=PromptCategory(data["category"]),
            is_default=data["is_default"],
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class UserSummary:
    """A summary of a user for admin purposes."""
    id: str
    email: str
    full_name: str
    role: str
    status: UserStatus
    created_at: datetime.datetime
    conversation_count: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSummary':
        """
        Create a UserSummary from a dictionary.
        
        Args:
            data: Dictionary containing user summary data
            
        Returns:
            UserSummary instance
        """
        return cls(
            id=data["id"],
            email=data["email"],
            full_name=data["full_name"],
            role=data["role"],
            status=UserStatus(data["status"]),
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            conversation_count=data["conversation_count"]
        )


@dataclass
class ConversationMetrics:
    """Metrics for conversations over a time period."""
    total_conversations: int
    active_users: int
    total_turns: int
    avg_turns_per_conversation: float
    avg_conversation_duration: float  # in seconds
    period: MetricsPeriod
    start_date: datetime.datetime
    end_date: datetime.datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], period: MetricsPeriod, start_date: datetime.datetime, end_date: datetime.datetime) -> 'ConversationMetrics':
        """
        Create a ConversationMetrics from a dictionary.
        
        Args:
            data: Dictionary containing metrics data
            period: Time period for the metrics
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            ConversationMetrics instance
        """
        return cls(
            total_conversations=data["total_conversations"],
            active_users=data["active_users"],
            total_turns=data["total_turns"],
            avg_turns_per_conversation=data["avg_turns_per_conversation"],
            avg_conversation_duration=data["avg_conversation_duration"],
            period=period,
            start_date=start_date,
            end_date=end_date
        )