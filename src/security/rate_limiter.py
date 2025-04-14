"""
Rate Limiter Module

This module provides rate limiting functionality for the voice agent application.
It implements rate limiting for authentication attempts and API requests.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple, Union
from collections import defaultdict, deque
import hashlib
import os

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for controlling request rates."""
    
    def __init__(self):
        """Initialize the rate limiter."""
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Store request counts for different keys and windows
        self._request_counts: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        
        # Default limits
        self.default_limits = {
            "auth": {
                "window": 300,  # 5 minutes
                "max_requests": 5
            },
            "api": {
                "window": 60,  # 1 minute
                "max_requests": 60
            },
            "voice": {
                "window": 60,  # 1 minute
                "max_requests": 30
            }
        }
        
    def check_rate_limit(
        self, 
        key: str, 
        limit_type: str = "api",
        increment: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a request exceeds the rate limit.
        
        Args:
            key: Identifier for the requester (e.g., IP address, user ID)
            limit_type: Type of rate limit to apply
            increment: Whether to increment the request count
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        with self._lock:
            # Get the limit configuration
            limit_config = self.default_limits.get(limit_type, self.default_limits["api"])
            window = limit_config["window"]
            max_requests = limit_config["max_requests"]
            
            # Hash the key for privacy
            hashed_key = self._hash_key(key)
            
            # Get the request queue for this key and limit type
            request_queue = self._request_counts[hashed_key][limit_type]
            
            # Current time
            current_time = time.time()
            
            # Remove expired timestamps
            while request_queue and request_queue[0] < current_time - window:
                request_queue.popleft()
                
            # Check if the limit is exceeded
            is_allowed = len(request_queue) < max_requests
            
            # Increment the count if requested and allowed
            if increment and is_allowed:
                request_queue.append(current_time)
                
            # Calculate remaining requests and reset time
            remaining = max(0, max_requests - len(request_queue))
            reset_time = 0 if not request_queue else int(request_queue[0] + window - current_time)
            
            # Prepare limit information
            limit_info = {
                "limit": max_requests,
                "remaining": remaining,
                "reset": reset_time,
                "window": window
            }
            
            # Log rate limit events
            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded for {limit_type}. "
                    f"Key: {hashed_key[:8]}..., "
                    f"Requests: {len(request_queue)}, "
                    f"Limit: {max_requests}, "
                    f"Window: {window}s"
                )
                
            return is_allowed, limit_info
            
    def reset_limits(self, key: str, limit_type: Optional[str] = None) -> None:
        """
        Reset rate limits for a key.
        
        Args:
            key: Identifier for the requester
            limit_type: Type of rate limit to reset, or None for all
        """
        with self._lock:
            hashed_key = self._hash_key(key)
            
            if limit_type:
                if hashed_key in self._request_counts and limit_type in self._request_counts[hashed_key]:
                    del self._request_counts[hashed_key][limit_type]
            else:
                if hashed_key in self._request_counts:
                    del self._request_counts[hashed_key]
                    
    def update_limit(self, limit_type: str, window: int, max_requests: int) -> None:
        """
        Update a rate limit configuration.
        
        Args:
            limit_type: Type of rate limit to update
            window: Time window in seconds
            max_requests: Maximum number of requests in the window
        """
        with self._lock:
            self.default_limits[limit_type] = {
                "window": window,
                "max_requests": max_requests
            }
            
    def _hash_key(self, key: str) -> str:
        """
        Hash a key for privacy.
        
        Args:
            key: Key to hash
            
        Returns:
            Hashed key
        """
        # Add a salt for additional security
        salt = os.environ.get("RATE_LIMIT_SALT", "default_salt")
        
        # Create a hash of the key
        return hashlib.sha256(f"{key}{salt}".encode()).hexdigest()
        
    def get_limit_headers(self, limit_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Get HTTP headers for rate limiting.
        
        Args:
            limit_info: Limit information from check_rate_limit
            
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "X-RateLimit-Limit": str(limit_info["limit"]),
            "X-RateLimit-Remaining": str(limit_info["remaining"]),
            "X-RateLimit-Reset": str(limit_info["reset"]),
            "X-RateLimit-Window": str(limit_info["window"])
        }


class IPRateLimiter(RateLimiter):
    """Rate limiter specifically for IP-based rate limiting."""
    
    def check_ip_rate_limit(
        self, 
        ip_address: str, 
        limit_type: str = "api",
        increment: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if an IP address exceeds the rate limit.
        
        Args:
            ip_address: IP address
            limit_type: Type of rate limit to apply
            increment: Whether to increment the request count
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        # Normalize the IP address
        normalized_ip = self._normalize_ip(ip_address)
        
        # Use the base class method
        return self.check_rate_limit(normalized_ip, limit_type, increment)
        
    def _normalize_ip(self, ip_address: str) -> str:
        """
        Normalize an IP address.
        
        Args:
            ip_address: IP address
            
        Returns:
            Normalized IP address
        """
        # Handle IPv4
        if "." in ip_address:
            # Use the first three octets for IPv4 (network portion)
            parts = ip_address.split(".")
            if len(parts) == 4:
                return ".".join(parts[:3]) + ".0"
                
        # Handle IPv6
        elif ":" in ip_address:
            # Use the first four segments for IPv6
            parts = ip_address.split(":")
            if len(parts) >= 4:
                return ":".join(parts[:4]) + "::"
                
        # Return as is if we can't normalize
        return ip_address


class UserRateLimiter(RateLimiter):
    """Rate limiter specifically for user-based rate limiting."""
    
    def check_user_rate_limit(
        self, 
        user_id: str, 
        limit_type: str = "api",
        increment: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a user exceeds the rate limit.
        
        Args:
            user_id: User ID
            limit_type: Type of rate limit to apply
            increment: Whether to increment the request count
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        # Prefix with "user:" to distinguish from other keys
        key = f"user:{user_id}"
        
        # Use the base class method
        return self.check_rate_limit(key, limit_type, increment)


# Create singleton instances
_rate_limiter = None
_ip_rate_limiter = None
_user_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """
    Get the singleton RateLimiter instance.
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

def get_ip_rate_limiter() -> IPRateLimiter:
    """
    Get the singleton IPRateLimiter instance.
    
    Returns:
        IPRateLimiter instance
    """
    global _ip_rate_limiter
    if _ip_rate_limiter is None:
        _ip_rate_limiter = IPRateLimiter()
    return _ip_rate_limiter

def get_user_rate_limiter() -> UserRateLimiter:
    """
    Get the singleton UserRateLimiter instance.
    
    Returns:
        UserRateLimiter instance
    """
    global _user_rate_limiter
    if _user_rate_limiter is None:
        _user_rate_limiter = UserRateLimiter()
    return _user_rate_limiter