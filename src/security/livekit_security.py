"""
LiveKit Security Module

This module provides security features for LiveKit integration, including:
- Room and participant name validation
- Token rate limiting
- Subscription rate limiting and limits
- RLS policy evaluation logging
"""

import re
import time
import uuid
from typing import Dict, Any, Optional, List, Tuple, Set, Union
from datetime import datetime, timedelta
import json

from loguru import logger
from supabase import Client

from src.config.config_service import get_config_service
from src.monitoring.security_monitoring import get_security_monitor


class LiveKitSecurityManager:
    """
    LiveKit Security Manager.
    
    This class provides security features for LiveKit integration:
    1. Room and participant name validation
    2. Token rate limiting
    3. Subscription rate limiting and limits
    4. RLS policy evaluation logging
    """
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the LiveKit security manager.
        
        Args:
            supabase_client: Optional Supabase client for database operations
        """
        self.config = get_config_service()
        self.supabase = supabase_client
        
        # Initialize security monitor if available
        self.security_monitor = get_security_monitor(supabase_client)
        
        # Load configuration with secure defaults
        self.token_rate_limit = self.config.get_int("LIVEKIT_TOKEN_RATE_LIMIT", 10)
        self.subscription_rate_limit = self.config.get_int("LIVEKIT_SUBSCRIPTION_RATE_LIMIT", 5)
        self.max_subscriptions_per_user = self.config.get_int("LIVEKIT_MAX_SUBSCRIPTIONS_PER_USER", 3)
        
        # Rate limit tracking
        self.token_requests: Dict[str, List[float]] = {}  # user_id -> list of timestamps
        self.subscription_requests: Dict[str, List[float]] = {}  # user_id -> list of timestamps
        
        # Active subscriptions
        self.active_subscriptions: Dict[str, Set[str]] = {}  # user_id -> set of subscription_ids
        
        # Compile regex patterns for validation
        self.room_name_pattern = re.compile(r'^[a-zA-Z0-9_-]{3,64}$')
        self.participant_name_pattern = re.compile(r'^[a-zA-Z0-9_-]{3,64}$')
        
        logger.info("LiveKit Security Manager initialized")
    
    def validate_room_name(self, room_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a LiveKit room name.
        
        Args:
            room_name: Room name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not room_name:
            return False, "Room name is required"
            
        room_name = room_name.strip()
        
        if len(room_name) < 3:
            return False, "Room name must be at least 3 characters long"
            
        if len(room_name) > 64:
            return False, "Room name must be at most 64 characters long"
            
        if not self.room_name_pattern.match(room_name):
            return False, "Room name can only contain letters, numbers, underscores, and hyphens"
            
        return True, None
    
    def validate_participant_name(self, participant_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a LiveKit participant name.
        
        Args:
            participant_name: Participant name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not participant_name:
            return False, "Participant name is required"
            
        participant_name = participant_name.strip()
        
        if len(participant_name) < 3:
            return False, "Participant name must be at least 3 characters long"
            
        if len(participant_name) > 64:
            return False, "Participant name must be at most 64 characters long"
            
        if not self.participant_name_pattern.match(participant_name):
            return False, "Participant name can only contain letters, numbers, underscores, and hyphens"
            
        return True, None
    
    def validate_token_rate_limit(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate token rate limit for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        now = time.time()
        window = 60  # 1 minute window
        
        # Initialize user if not exists
        if user_id not in self.token_requests:
            self.token_requests[user_id] = []
            
        # Remove old requests
        self.token_requests[user_id] = [t for t in self.token_requests[user_id] if now - t < window]
        
        # Check rate limit
        count = len(self.token_requests[user_id])
        is_allowed = count < self.token_rate_limit
        
        # Add current request
        if is_allowed:
            self.token_requests[user_id].append(now)
            
        # Calculate reset time
        reset_at = now + window if count == 0 else self.token_requests[user_id][0] + window
        
        # Create limit info
        limit_info = {
            "count": count,
            "limit": self.token_rate_limit,
            "remaining": max(0, self.token_rate_limit - count),
            "reset_at": reset_at
        }
        
        # Log rate limit violation if not allowed
        if not is_allowed and self.security_monitor:
            self.security_monitor.log_security_event(
                event_type="token_rate_limit_exceeded",
                user_id=user_id,
                details={
                    "count": count,
                    "limit": self.token_rate_limit,
                    "window": window
                },
                severity="warning"
            )
            
        return is_allowed, limit_info
    
    def validate_subscription_rate_limit(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate subscription rate limit for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        now = time.time()
        window = 60  # 1 minute window
        
        # Initialize user if not exists
        if user_id not in self.subscription_requests:
            self.subscription_requests[user_id] = []
            
        # Remove old requests
        self.subscription_requests[user_id] = [t for t in self.subscription_requests[user_id] if now - t < window]
        
        # Check rate limit
        count = len(self.subscription_requests[user_id])
        is_allowed = count < self.subscription_rate_limit
        
        # Add current request
        if is_allowed:
            self.subscription_requests[user_id].append(now)
            
        # Calculate reset time
        reset_at = now + window if count == 0 else self.subscription_requests[user_id][0] + window
        
        # Create limit info
        limit_info = {
            "count": count,
            "limit": self.subscription_rate_limit,
            "remaining": max(0, self.subscription_rate_limit - count),
            "reset_at": reset_at
        }
        
        # Log rate limit violation if not allowed
        if not is_allowed and self.security_monitor:
            self.security_monitor.log_security_event(
                event_type="subscription_rate_limit_exceeded",
                user_id=user_id,
                details={
                    "count": count,
                    "limit": self.subscription_rate_limit,
                    "window": window
                },
                severity="warning"
            )
            
        return is_allowed, limit_info
    
    def validate_subscription_limit(self, user_id: str, subscription_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate subscription limit for a user.
        
        Args:
            user_id: User ID
            subscription_id: Subscription ID
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        # Initialize user if not exists
        if user_id not in self.active_subscriptions:
            self.active_subscriptions[user_id] = set()
            
        # Check subscription limit
        count = len(self.active_subscriptions[user_id])
        is_allowed = count < self.max_subscriptions_per_user
        
        # Add current subscription
        if is_allowed:
            self.active_subscriptions[user_id].add(subscription_id)
            
        # Create limit info
        limit_info = {
            "count": count,
            "limit": self.max_subscriptions_per_user,
            "remaining": max(0, self.max_subscriptions_per_user - count),
            "subscriptions": list(self.active_subscriptions[user_id])
        }
        
        # Log subscription limit violation if not allowed
        if not is_allowed and self.security_monitor:
            self.security_monitor.log_security_event(
                event_type="subscription_limit_exceeded",
                user_id=user_id,
                details={
                    "count": count,
                    "limit": self.max_subscriptions_per_user,
                    "subscriptions": list(self.active_subscriptions[user_id])
                },
                severity="warning"
            )
            
        return is_allowed, limit_info
    
    def remove_subscription(self, user_id: str, subscription_id: str) -> bool:
        """
        Remove a subscription for a user.
        
        Args:
            user_id: User ID
            subscription_id: Subscription ID
            
        Returns:
            True if removed, False otherwise
        """
        if user_id in self.active_subscriptions and subscription_id in self.active_subscriptions[user_id]:
            self.active_subscriptions[user_id].remove(subscription_id)
            return True
        return False
    
    def log_rls_policy_evaluation(
        self, 
        user_id: str, 
        resource_type: str, 
        resource_id: str, 
        action: str, 
        is_allowed: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a Row Level Security (RLS) policy evaluation.
        
        Args:
            user_id: User ID
            resource_type: Type of resource (e.g., "room", "participant")
            resource_id: ID of the resource
            action: Action being performed (e.g., "join", "publish")
            is_allowed: Whether the action was allowed
            context: Optional additional context
        """
        if self.security_monitor:
            self.security_monitor.log_rls_policy_evaluation(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                is_allowed=is_allowed,
                context=context
            )
        else:
            # Fallback to regular logging if security monitor is not available
            severity = "info" if is_allowed else "warning"
            log_message = f"RLS policy evaluation: {action} on {resource_type}/{resource_id} by user {user_id} - {'allowed' if is_allowed else 'denied'}"
            
            if severity == "warning":
                logger.warning(log_message)
            else:
                logger.info(log_message)


# Singleton instance
_livekit_security_manager = None

def get_livekit_security_manager(supabase_client=None) -> LiveKitSecurityManager:
    """
    Get the singleton LiveKitSecurityManager instance.
    
    Args:
        supabase_client: Optional Supabase client for database operations
        
    Returns:
        LiveKitSecurityManager instance
    """
    global _livekit_security_manager
    if _livekit_security_manager is None:
        _livekit_security_manager = LiveKitSecurityManager(supabase_client)
    return _livekit_security_manager