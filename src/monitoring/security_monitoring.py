"""
Security Monitoring Module

This module provides security monitoring capabilities, including:
- Audit logging for security events
- RLS policy evaluation logging
- Resource usage monitoring
- Security alerts for suspicious activity
"""

import time
import json
import uuid
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field

from loguru import logger
from supabase import Client

from src.config.config_service import get_config_service


@dataclass
class ResourceUsageMetrics:
    """Resource usage metrics for a user."""
    room_count: int = 0
    participant_count: int = 0
    subscription_count: int = 0
    token_count: int = 0
    bandwidth_usage: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_updated: float = field(default_factory=time.time)


class SecurityMonitor:
    """
    Security Monitor for tracking security events and resource usage.
    
    This class provides:
    1. Audit logging for security events
    2. RLS policy evaluation logging
    3. Resource usage monitoring
    4. Security alerts for suspicious activity
    """
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the security monitor.
        
        Args:
            supabase_client: Optional Supabase client for database operations
        """
        self.config = get_config_service()
        self.supabase = supabase_client
        
        # Load configuration with secure defaults
        self.room_count_threshold = self.config.get_int("SECURITY_ROOM_COUNT_THRESHOLD", 100)
        self.participant_count_threshold = self.config.get_int("SECURITY_PARTICIPANT_COUNT_THRESHOLD", 1000)
        self.subscription_count_threshold = self.config.get_int("SECURITY_SUBSCRIPTION_COUNT_THRESHOLD", 500)
        self.token_count_threshold = self.config.get_int("SECURITY_TOKEN_COUNT_THRESHOLD", 1000)
        self.bandwidth_usage_threshold = self.config.get_float("SECURITY_BANDWIDTH_USAGE_THRESHOLD", 1000.0)
        self.alert_cooldown = self.config.get_int("SECURITY_ALERT_COOLDOWN", 3600)  # 1 hour
        
        # Resource usage metrics by user ID
        self.resource_metrics: Dict[str, ResourceUsageMetrics] = {}
        
        # Recent security events by user ID
        self.recent_events: Dict[str, List[Dict[str, Any]]] = {}
        
        # Recent alerts by user ID and type
        self.recent_alerts: Dict[str, Dict[str, float]] = {}
        
        logger.info("Security Monitor initialized")
    
    def log_security_event(
        self, 
        event_type: str, 
        user_id: str, 
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            user_id: User ID
            details: Optional event details
            severity: Event severity (info, warning, error)
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Create event record
        event = {
            "id": event_id,
            "type": event_type,
            "user_id": user_id,
            "details": details or {},
            "severity": severity,
            "timestamp": timestamp.isoformat(),
            "epoch": timestamp.timestamp()
        }
        
        # Add to recent events
        if user_id not in self.recent_events:
            self.recent_events[user_id] = []
        self.recent_events[user_id].append(event)
        
        # Limit recent events to 100 per user
        if len(self.recent_events[user_id]) > 100:
            self.recent_events[user_id] = self.recent_events[user_id][-100:]
        
        # Log to database if available
        if self.supabase:
            try:
                self.supabase.table("security_events").insert(event).execute()
            except Exception as e:
                logger.error(f"Failed to log security event to database: {str(e)}")
        
        # Log to console
        log_message = f"Security event: {event_type} for user {user_id}"
        if details:
            log_message += f" - {json.dumps(details)}"
            
        if severity == "error":
            logger.error(log_message)
        elif severity == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        # Check for suspicious activity
        self._check_suspicious_activity(user_id, event_type, details, severity)
    
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
        # Create event details
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "is_allowed": is_allowed
        }
        
        # Add context if provided
        if context:
            details["context"] = context
            
        # Log as security event
        severity = "info" if is_allowed else "warning"
        self.log_security_event(
            event_type="rls_policy_evaluation",
            user_id=user_id,
            details=details,
            severity=severity
        )
    
    def log_livekit_resource_usage(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Log LiveKit resource usage.
        
        Args:
            user_id: User ID
            resource_type: Type of resource (e.g., "room", "participant")
            resource_id: ID of the resource
            metrics: Resource usage metrics
        """
        # Create event details
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "metrics": metrics
        }
        
        # Log as security event
        self.log_security_event(
            event_type="livekit_resource_usage",
            user_id=user_id,
            details=details,
            severity="info"
        )
    
    def update_resource_metrics(
        self,
        user_id: str,
        metrics: ResourceUsageMetrics
    ) -> None:
        """
        Update resource usage metrics for a user.
        
        Args:
            user_id: User ID
            metrics: Resource usage metrics
        """
        # Update metrics
        self.resource_metrics[user_id] = metrics
        
        # Check thresholds
        self._check_resource_thresholds(user_id, metrics)
        
        # Log to database if available
        if self.supabase:
            try:
                self.supabase.table("resource_metrics").upsert({
                    "user_id": user_id,
                    "metrics": asdict(metrics),
                    "updated_at": datetime.now().isoformat()
                }).execute()
            except Exception as e:
                logger.error(f"Failed to update resource metrics in database: {str(e)}")
    
    def get_user_metrics(self, user_id: str) -> Optional[ResourceUsageMetrics]:
        """
        Get resource usage metrics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            ResourceUsageMetrics or None if not found
        """
        return self.resource_metrics.get(user_id)
    
    def get_user_events(
        self, 
        user_id: str, 
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent security events for a user.
        
        Args:
            user_id: User ID
            event_type: Optional event type filter
            limit: Maximum number of events to return
            
        Returns:
            List of security events
        """
        if user_id not in self.recent_events:
            return []
            
        events = self.recent_events[user_id]
        
        # Filter by event type if specified
        if event_type:
            events = [e for e in events if e["type"] == event_type]
            
        # Sort by timestamp (newest first)
        events = sorted(events, key=lambda e: e["epoch"], reverse=True)
        
        # Limit results
        return events[:limit]
    
    def _check_resource_thresholds(self, user_id: str, metrics: ResourceUsageMetrics) -> None:
        """
        Check resource usage thresholds and generate alerts if exceeded.
        
        Args:
            user_id: User ID
            metrics: Resource usage metrics
        """
        now = time.time()
        
        # Check room count threshold
        if metrics.room_count > self.room_count_threshold:
            self._create_alert(
                user_id=user_id,
                alert_type="room_count_exceeded",
                details={
                    "room_count": metrics.room_count,
                    "threshold": self.room_count_threshold
                },
                now=now
            )
            
        # Check participant count threshold
        if metrics.participant_count > self.participant_count_threshold:
            self._create_alert(
                user_id=user_id,
                alert_type="participant_count_exceeded",
                details={
                    "participant_count": metrics.participant_count,
                    "threshold": self.participant_count_threshold
                },
                now=now
            )
            
        # Check subscription count threshold
        if metrics.subscription_count > self.subscription_count_threshold:
            self._create_alert(
                user_id=user_id,
                alert_type="subscription_count_exceeded",
                details={
                    "subscription_count": metrics.subscription_count,
                    "threshold": self.subscription_count_threshold
                },
                now=now
            )
            
        # Check token count threshold
        if metrics.token_count > self.token_count_threshold:
            self._create_alert(
                user_id=user_id,
                alert_type="token_count_exceeded",
                details={
                    "token_count": metrics.token_count,
                    "threshold": self.token_count_threshold
                },
                now=now
            )
            
        # Check bandwidth usage threshold
        if metrics.bandwidth_usage > self.bandwidth_usage_threshold:
            self._create_alert(
                user_id=user_id,
                alert_type="bandwidth_usage_exceeded",
                details={
                    "bandwidth_usage": metrics.bandwidth_usage,
                    "threshold": self.bandwidth_usage_threshold
                },
                now=now
            )
    
    def _check_suspicious_activity(
        self, 
        user_id: str, 
        event_type: str, 
        details: Optional[Dict[str, Any]],
        severity: str
    ) -> None:
        """
        Check for suspicious activity patterns.
        
        Args:
            user_id: User ID
            event_type: Event type
            details: Event details
            severity: Event severity
        """
        if severity == "error" or severity == "warning":
            # Count recent high-severity events
            recent_events = self.get_user_events(user_id, limit=100)
            high_severity_count = sum(1 for e in recent_events if e["severity"] in ["error", "warning"])
            
            # Alert if there are multiple high-severity events
            if high_severity_count >= 5:
                self._create_alert(
                    user_id=user_id,
                    alert_type="multiple_high_severity_events",
                    details={
                        "count": high_severity_count,
                        "recent_events": [e["type"] for e in recent_events[:5] if e["severity"] in ["error", "warning"]]
                    }
                )
                
        # Check for inactive users with high resource usage
        if user_id in self.resource_metrics:
            metrics = self.resource_metrics[user_id]
            now = time.time()
            
            # If last update was more than 1 hour ago but resources are still high
            if (now - metrics.last_updated > 3600 and 
                (metrics.room_count > 10 or 
                 metrics.participant_count > 20 or 
                 metrics.subscription_count > 10)):
                self._create_alert(
                    user_id=user_id,
                    alert_type="inactive_user_high_resources",
                    details={
                        "last_active": metrics.last_updated,
                        "inactive_for": now - metrics.last_updated,
                        "room_count": metrics.room_count,
                        "participant_count": metrics.participant_count,
                        "subscription_count": metrics.subscription_count
                    }
                )
    
    def _create_alert(
        self, 
        user_id: str, 
        alert_type: str, 
        details: Dict[str, Any],
        now: Optional[float] = None
    ) -> None:
        """
        Create a security alert.
        
        Args:
            user_id: User ID
            alert_type: Alert type
            details: Alert details
            now: Current timestamp (optional)
        """
        if now is None:
            now = time.time()
            
        # Check alert cooldown
        if user_id not in self.recent_alerts:
            self.recent_alerts[user_id] = {}
            
        if alert_type in self.recent_alerts[user_id]:
            last_alert = self.recent_alerts[user_id][alert_type]
            if now - last_alert < self.alert_cooldown:
                # Alert is in cooldown period
                return
                
        # Update last alert time
        self.recent_alerts[user_id][alert_type] = now
        
        # Create alert
        alert_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        alert = {
            "id": alert_id,
            "type": alert_type,
            "user_id": user_id,
            "details": details,
            "timestamp": timestamp.isoformat(),
            "epoch": timestamp.timestamp()
        }
        
        # Log to database if available
        if self.supabase:
            try:
                self.supabase.table("security_alerts").insert(alert).execute()
            except Exception as e:
                logger.error(f"Failed to log security alert to database: {str(e)}")
        
        # Log to console
        logger.warning(f"Security alert: {alert_type} for user {user_id} - {json.dumps(details)}")


# Singleton instance
_security_monitor = None

def get_security_monitor(supabase_client=None) -> SecurityMonitor:
    """
    Get the singleton SecurityMonitor instance.
    
    Args:
        supabase_client: Optional Supabase client for database operations
        
    Returns:
        SecurityMonitor instance
    """
    global _security_monitor
    if _security_monitor is None:
        _security_monitor = SecurityMonitor(supabase_client)
    return _security_monitor