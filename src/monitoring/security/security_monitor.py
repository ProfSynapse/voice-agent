"""
Security Monitor Module

This module provides security monitoring functionality for the Voice Agent application.
"""

import time
import logging
import json
import os
import ipaddress
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import deque, defaultdict, Counter
from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SecurityEvent(BaseModel):
    """Model for security events."""
    event_id: str
    event_type: str
    timestamp: float
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    status_code: Optional[int] = None
    details: Dict[str, Any] = {}
    severity: str = "info"

class AuthEvent(BaseModel):
    """Model for authentication events."""
    event_id: str
    timestamp: float
    event_type: str  # login, logout, login_failed, password_reset, etc.
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    failure_reason: Optional[str] = None
    details: Dict[str, Any] = {}

class APIUsageEvent(BaseModel):
    """Model for API usage events."""
    event_id: str
    timestamp: float
    endpoint: str
    method: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    status_code: int
    response_time: float
    request_size: Optional[int] = None
    response_size: Optional[int] = None
    details: Dict[str, Any] = {}

class SecurityMonitor:
    """
    Security Monitor for the Voice Agent application.
    
    This class provides security monitoring functionality to track authentication attempts,
    API usage patterns, and detect anomalies.
    """
    
    def __init__(self):
        """Initialize the security monitor."""
        self.security_events = deque(maxlen=10000)
        self.auth_events = deque(maxlen=10000)
        self.api_usage_events = deque(maxlen=10000)
        
        self.ip_blacklist = set()
        self.ip_whitelist = set()
        self.user_agent_blacklist = set()
        self.path_blacklist = set()
        
        self.failed_login_attempts = defaultdict(list)  # IP -> list of timestamps
        self.suspicious_ips = set()
        self.suspicious_users = set()
        
        self.rate_limits = {}  # path -> (limit, window)
        self.rate_limit_counters = defaultdict(lambda: defaultdict(list))  # path -> (ip -> list of timestamps)
        
        self.alert_handlers = []
        self.data_dir = "data/security"
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Default settings
        self.max_failed_logins = 5
        self.failed_login_window = 300  # 5 minutes
        self.default_rate_limit = (100, 60)  # 100 requests per minute
    
    def register_with_app(self, app: FastAPI):
        """
        Register security monitoring middleware and endpoints with the FastAPI application.
        
        Args:
            app: The FastAPI application
        """
        # Add middleware for security monitoring
        @app.middleware("http")
        async def security_middleware(request: Request, call_next):
            # Get client info
            ip = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            path = request.url.path
            method = request.method
            
            # Check blacklists
            if self._is_blacklisted(ip, user_agent, path):
                self.log_security_event(
                    event_type="blacklist_blocked",
                    ip_address=ip,
                    user_agent=user_agent,
                    request_path=path,
                    request_method=method,
                    severity="warning",
                    details={"reason": "Blacklisted IP, user agent, or path"}
                )
                
                return Response(
                    content=json.dumps({"error": "Access denied"}),
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json"
                )
            
            # Check rate limits
            if not self._check_rate_limit(path, ip):
                self.log_security_event(
                    event_type="rate_limit_exceeded",
                    ip_address=ip,
                    user_agent=user_agent,
                    request_path=path,
                    request_method=method,
                    severity="warning",
                    details={"reason": "Rate limit exceeded"}
                )
                
                return Response(
                    content=json.dumps({"error": "Rate limit exceeded"}),
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json"
                )
            
            # Start timer for API usage tracking
            start_time = time.time()
            
            # Process request
            response = await call_next(request)
            
            # End timer
            duration = time.time() - start_time
            
            # Track API usage
            self.track_api_usage(
                endpoint=path,
                method=method,
                user_id=request.cookies.get("user_id"),
                ip_address=ip,
                status_code=response.status_code,
                response_time=duration
            )
            
            return response
        
        # Register security event endpoint
        @app.get("/security/events", status_code=status.HTTP_200_OK)
        async def get_security_events(limit: int = 100, event_type: Optional[str] = None, 
                                   severity: Optional[str] = None):
            """Get recent security events with optional filtering."""
            events = self.get_security_events(limit, event_type, severity)
            return {
                "events": events,
                "count": len(events),
                "timestamp": time.time()
            }
        
        # Register authentication events endpoint
        @app.get("/security/auth-events", status_code=status.HTTP_200_OK)
        async def get_auth_events(limit: int = 100, event_type: Optional[str] = None, 
                               user_id: Optional[str] = None):
            """Get recent authentication events with optional filtering."""
            events = self.get_auth_events(limit, event_type, user_id)
            return {
                "events": events,
                "count": len(events),
                "timestamp": time.time()
            }
        
        # Register API usage endpoint
        @app.get("/security/api-usage", status_code=status.HTTP_200_OK)
        async def get_api_usage(limit: int = 100, endpoint: Optional[str] = None, 
                             user_id: Optional[str] = None):
            """Get recent API usage events with optional filtering."""
            events = self.get_api_usage_events(limit, endpoint, user_id)
            return {
                "events": events,
                "count": len(events),
                "timestamp": time.time()
            }
        
        # Register suspicious activity endpoint
        @app.get("/security/suspicious", status_code=status.HTTP_200_OK)
        async def get_suspicious_activity():
            """Get suspicious IPs and users."""
            return {
                "suspicious_ips": list(self.suspicious_ips),
                "suspicious_users": list(self.suspicious_users),
                "timestamp": time.time()
            }
    
    def log_security_event(self, event_type: str, severity: str = "info", 
                          user_id: Optional[str] = None, ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None, request_path: Optional[str] = None,
                          request_method: Optional[str] = None, status_code: Optional[int] = None,
                          details: Dict[str, Any] = None) -> str:
        """
        Log a security event.
        
        Args:
            event_type: The type of security event
            severity: The severity level (info, warning, error, critical)
            user_id: The user ID
            ip_address: The client IP address
            user_agent: The client user agent
            request_path: The request path
            request_method: The request method
            status_code: The response status code
            details: Additional details about the event
            
        Returns:
            The event ID
        """
        event_id = f"sec_{int(time.time())}_{hash(event_type)}"
        
        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=time.time(),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
            details=details or {},
            severity=severity
        )
        
        # Add to events
        self.security_events.append(event.dict())
        
        # Save to file
        self._save_security_event(event)
        
        # Log using standard logger
        log_level = self._get_log_level(severity)
        logger.log(log_level, f"Security event: {event_type} - {details}")
        
        # Check if this is a high severity event
        if severity in ["error", "critical"]:
            self._trigger_alert(event)
        
        return event_id
    
    def log_auth_event(self, event_type: str, success: bool = True, 
                      user_id: Optional[str] = None, ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None, failure_reason: Optional[str] = None,
                      details: Dict[str, Any] = None) -> str:
        """
        Log an authentication event.
        
        Args:
            event_type: The type of auth event (login, logout, etc.)
            success: Whether the authentication was successful
            user_id: The user ID
            ip_address: The client IP address
            user_agent: The client user agent
            failure_reason: The reason for failure (if not successful)
            details: Additional details about the event
            
        Returns:
            The event ID
        """
        event_id = f"auth_{int(time.time())}_{hash(event_type)}"
        
        event = AuthEvent(
            event_id=event_id,
            timestamp=time.time(),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
            details=details or {}
        )
        
        # Add to events
        self.auth_events.append(event.dict())
        
        # Save to file
        self._save_auth_event(event)
        
        # Check for failed login attempts
        if event_type == "login" and not success and ip_address:
            self._track_failed_login(ip_address)
        
        # Log using standard logger
        if success:
            logger.info(f"Auth event: {event_type} - User: {user_id or 'anonymous'}")
        else:
            logger.warning(f"Auth event: {event_type} failed - User: {user_id or 'anonymous'} - Reason: {failure_reason}")
        
        return event_id
    
    def track_api_usage(self, endpoint: str, method: str, status_code: int, 
                       response_time: float, user_id: Optional[str] = None,
                       ip_address: Optional[str] = None, request_size: Optional[int] = None,
                       response_size: Optional[int] = None, details: Dict[str, Any] = None) -> str:
        """
        Track API usage.
        
        Args:
            endpoint: The API endpoint
            method: The HTTP method
            status_code: The response status code
            response_time: The response time in seconds
            user_id: The user ID
            ip_address: The client IP address
            request_size: The request size in bytes
            response_size: The response size in bytes
            details: Additional details
            
        Returns:
            The event ID
        """
        event_id = f"api_{int(time.time())}_{hash(endpoint)}"
        
        event = APIUsageEvent(
            event_id=event_id,
            timestamp=time.time(),
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            ip_address=ip_address,
            status_code=status_code,
            response_time=response_time,
            request_size=request_size,
            response_size=response_size,
            details=details or {}
        )
        
        # Add to events
        self.api_usage_events.append(event.dict())
        
        # Save to file
        self._save_api_usage_event(event)
        
        # Check for anomalies
        if response_time > 5.0:  # More than 5 seconds
            self.log_security_event(
                event_type="slow_api_response",
                severity="warning",
                user_id=user_id,
                ip_address=ip_address,
                request_path=endpoint,
                request_method=method,
                status_code=status_code,
                details={
                    "response_time": response_time,
                    "threshold": 5.0
                }
            )
        
        if status_code >= 500:
            self.log_security_event(
                event_type="api_server_error",
                severity="error",
                user_id=user_id,
                ip_address=ip_address,
                request_path=endpoint,
                request_method=method,
                status_code=status_code,
                details=details
            )
        
        return event_id
    
    def get_security_events(self, limit: int = 100, event_type: Optional[str] = None, 
                           severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent security events with optional filtering.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            severity: Filter by severity level
            
        Returns:
            A list of security events
        """
        filtered_events = []
        
        for event in reversed(self.security_events):  # Most recent first
            if event_type and event["event_type"] != event_type:
                continue
                
            if severity and event["severity"] != severity:
                continue
                
            filtered_events.append(event)
            
            if len(filtered_events) >= limit:
                break
        
        return filtered_events
    
    def get_auth_events(self, limit: int = 100, event_type: Optional[str] = None, 
                       user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent authentication events with optional filtering.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            user_id: Filter by user ID
            
        Returns:
            A list of authentication events
        """
        filtered_events = []
        
        for event in reversed(self.auth_events):  # Most recent first
            if event_type and event["event_type"] != event_type:
                continue
                
            if user_id and event["user_id"] != user_id:
                continue
                
            filtered_events.append(event)
            
            if len(filtered_events) >= limit:
                break
        
        return filtered_events
    
    def get_api_usage_events(self, limit: int = 100, endpoint: Optional[str] = None, 
                            user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent API usage events with optional filtering.
        
        Args:
            limit: Maximum number of events to return
            endpoint: Filter by endpoint
            user_id: Filter by user ID
            
        Returns:
            A list of API usage events
        """
        filtered_events = []
        
        for event in reversed(self.api_usage_events):  # Most recent first
            if endpoint and event["endpoint"] != endpoint:
                continue
                
            if user_id and event["user_id"] != user_id:
                continue
                
            filtered_events.append(event)
            
            if len(filtered_events) >= limit:
                break
        
        return filtered_events
    
    def add_to_blacklist(self, ip: Optional[str] = None, user_agent: Optional[str] = None, 
                        path: Optional[str] = None):
        """
        Add an IP, user agent, or path to the blacklist.
        
        Args:
            ip: The IP address to blacklist
            user_agent: The user agent to blacklist
            path: The path to blacklist
        """
        if ip:
            self.ip_blacklist.add(ip)
            logger.warning(f"Added IP to blacklist: {ip}")
        
        if user_agent:
            self.user_agent_blacklist.add(user_agent)
            logger.warning(f"Added user agent to blacklist: {user_agent}")
        
        if path:
            self.path_blacklist.add(path)
            logger.warning(f"Added path to blacklist: {path}")
    
    def add_to_whitelist(self, ip: str):
        """
        Add an IP to the whitelist.
        
        Args:
            ip: The IP address to whitelist
        """
        self.ip_whitelist.add(ip)
        logger.info(f"Added IP to whitelist: {ip}")
    
    def set_rate_limit(self, path: str, limit: int, window: int):
        """
        Set a rate limit for a path.
        
        Args:
            path: The path to rate limit
            limit: The maximum number of requests
            window: The time window in seconds
        """
        self.rate_limits[path] = (limit, window)
        logger.info(f"Set rate limit for {path}: {limit} requests per {window} seconds")
    
    def add_alert_handler(self, handler):
        """
        Add an alert handler to be called when a security event occurs.
        
        Args:
            handler: A function that takes a security event
        """
        self.alert_handlers.append(handler)
    
    def _is_blacklisted(self, ip: Optional[str], user_agent: Optional[str], 
                       path: Optional[str]) -> bool:
        """
        Check if an IP, user agent, or path is blacklisted.
        
        Args:
            ip: The IP address
            user_agent: The user agent
            path: The path
            
        Returns:
            True if blacklisted, False otherwise
        """
        # Check whitelist first
        if ip and ip in self.ip_whitelist:
            return False
        
        # Check blacklists
        if ip and ip in self.ip_blacklist:
            return True
        
        if user_agent and any(pattern in user_agent for pattern in self.user_agent_blacklist):
            return True
        
        if path and any(pattern in path for pattern in self.path_blacklist):
            return True
        
        # Check suspicious IPs
        if ip and ip in self.suspicious_ips:
            return True
        
        return False
    
    def _check_rate_limit(self, path: str, ip: Optional[str]) -> bool:
        """
        Check if a request exceeds the rate limit.
        
        Args:
            path: The request path
            ip: The client IP address
            
        Returns:
            True if within rate limit, False otherwise
        """
        if not ip:
            return True
        
        # Get rate limit for path
        limit, window = self.rate_limits.get(path, self.default_rate_limit)
        
        # Get timestamps for this path and IP
        timestamps = self.rate_limit_counters[path][ip]
        
        # Add current timestamp
        now = time.time()
        timestamps.append(now)
        
        # Remove old timestamps
        while timestamps and timestamps[0] < now - window:
            timestamps.pop(0)
        
        # Check if count exceeds limit
        return len(timestamps) <= limit
    
    def _track_failed_login(self, ip: str):
        """
        Track a failed login attempt.
        
        Args:
            ip: The client IP address
        """
        now = time.time()
        
        # Add current timestamp
        self.failed_login_attempts[ip].append(now)
        
        # Remove old timestamps
        while (self.failed_login_attempts[ip] and 
               self.failed_login_attempts[ip][0] < now - self.failed_login_window):
            self.failed_login_attempts[ip].pop(0)
        
        # Check if count exceeds threshold
        if len(self.failed_login_attempts[ip]) >= self.max_failed_logins:
            self.suspicious_ips.add(ip)
            
            self.log_security_event(
                event_type="brute_force_attempt",
                severity="critical",
                ip_address=ip,
                details={
                    "failed_attempts": len(self.failed_login_attempts[ip]),
                    "window": self.failed_login_window
                }
            )
    
    def _trigger_alert(self, event: SecurityEvent):
        """
        Trigger an alert for a security event.
        
        Args:
            event: The security event
        """
        for handler in self.alert_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")
    
    def _get_log_level(self, severity: str) -> int:
        """
        Get the logging level for a severity.
        
        Args:
            severity: The severity level
            
        Returns:
            The logging level
        """
        if severity == "critical":
            return logging.CRITICAL
        elif severity == "error":
            return logging.ERROR
        elif severity == "warning":
            return logging.WARNING
        else:
            return logging.INFO
    
    def _save_security_event(self, event: SecurityEvent):
        """
        Save a security event to a file.
        
        Args:
            event: The security event
        """
        try:
            # Create filename based on date
            date_str = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d")
            filename = os.path.join(self.data_dir, f"security-events-{date_str}.jsonl")
            
            # Write event to file
            with open(filename, "a") as f:
                f.write(json.dumps(event.dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to save security event to file: {str(e)}")
    
    def _save_auth_event(self, event: AuthEvent):
        """
        Save an authentication event to a file.
        
        Args:
            event: The authentication event
        """
        try:
            # Create filename based on date
            date_str = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d")
            filename = os.path.join(self.data_dir, f"auth-events-{date_str}.jsonl")
            
            # Write event to file
            with open(filename, "a") as f:
                f.write(json.dumps(event.dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to save auth event to file: {str(e)}")
    
    def _save_api_usage_event(self, event: APIUsageEvent):
        """
        Save an API usage event to a file.
        
        Args:
            event: The API usage event
        """
        try:
            # Create filename based on date
            date_str = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d")
            filename = os.path.join(self.data_dir, f"api-usage-{date_str}.jsonl")
            
            # Write event to file
            with open(filename, "a") as f:
                f.write(json.dumps(event.dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to save API usage event to file: {str(e)}")

# Create a singleton instance
security_monitor = SecurityMonitor()