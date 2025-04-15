"""
Authentication Security Module

This module provides security-focused authentication functions.
"""

from typing import Optional, Dict, Any, Tuple
import logging

from supabase import Client
from loguru import logger

from src.auth.models import User, UserRole, AuthResult
from src.security.input_validation import get_input_validator
from src.security.token_validation import get_token_validator
from src.security.rate_limiter import get_user_rate_limiter, get_ip_rate_limiter
from src.security.error_handling import get_secure_error_handler


class AuthSecurityService:
    """
    Authentication security service that handles security-focused authentication functions.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the authentication security service.
        
        Args:
            supabase_client: Supabase client
        """
        self.supabase = supabase_client
        
        # Initialize security components
        self.input_validator = get_input_validator()
        self.token_validator = get_token_validator()
        self.user_rate_limiter = get_user_rate_limiter()
        self.ip_rate_limiter = get_ip_rate_limiter()
        self.error_handler = get_secure_error_handler()
    
    def validate_login_attempt(self, ip_address: Optional[str]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a login attempt using rate limiting.
        
        Args:
            ip_address: IP address of the request
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        if not ip_address:
            return True, None
            
        is_allowed, limit_info = self.ip_rate_limiter.check_ip_rate_limit(
            ip_address, 
            limit_type="auth", 
            increment=False
        )
        
        if not is_allowed:
            self.error_handler.log_security_event(
                "login_rate_limit_exceeded",
                {"ip_address": ip_address, "limit_info": limit_info},
                severity="warning"
            )
            
        return is_allowed, limit_info
    
    def validate_registration_attempt(self, ip_address: Optional[str]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a registration attempt using rate limiting.
        
        Args:
            ip_address: IP address of the request
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        if not ip_address:
            return True, None
            
        is_allowed, limit_info = self.ip_rate_limiter.check_ip_rate_limit(
            ip_address, 
            limit_type="auth", 
            increment=False
        )
        
        if not is_allowed:
            self.error_handler.log_security_event(
                "registration_rate_limit_exceeded",
                {"ip_address": ip_address, "limit_info": limit_info},
                severity="warning"
            )
            
        return is_allowed, limit_info
    
    def validate_password_reset_attempt(self, ip_address: Optional[str]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a password reset attempt using rate limiting.
        
        Args:
            ip_address: IP address of the request
            
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        if not ip_address:
            return True, None
            
        is_allowed, limit_info = self.ip_rate_limiter.check_ip_rate_limit(
            ip_address, 
            limit_type="auth", 
            increment=False
        )
        
        if not is_allowed:
            self.error_handler.log_security_event(
                "password_reset_rate_limit_exceeded",
                {"ip_address": ip_address, "limit_info": limit_info},
                severity="warning"
            )
            
        return is_allowed, limit_info
    
    def increment_auth_attempt(self, ip_address: Optional[str]) -> None:
        """
        Increment the authentication attempt counter.
        
        Args:
            ip_address: IP address of the request
        """
        if ip_address:
            self.ip_rate_limiter.check_ip_rate_limit(
                ip_address, 
                limit_type="auth", 
                increment=True
            )
    
    def reset_auth_attempts(self, ip_address: Optional[str]) -> None:
        """
        Reset the authentication attempt counter.
        
        Args:
            ip_address: IP address of the request
        """
        if ip_address:
            self.ip_rate_limiter.reset_limits(ip_address, "auth")
    
    def validate_email(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.input_validator.validate_email(email)
    
    def validate_password(self, password: str, username: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate a password.
        
        Args:
            password: Password to validate
            username: Username to check against
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.input_validator.validate_password(password, username)
    
    def validate_text(self, text: str, min_length: int = 1, max_length: int = 1000) -> Tuple[bool, Optional[str]]:
        """
        Validate text input.
        
        Args:
            text: Text to validate
            min_length: Minimum length
            max_length: Maximum length
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.input_validator.validate_text(text, min_length, max_length)
    
    def validate_session_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate a session token.
        
        Args:
            token: Session token to validate
            
        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        return self.token_validator.validate_token(token)
    
    def handle_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle an exception securely.
        
        Args:
            exc: Exception to handle
            context: Optional context information
            
        Returns:
            Sanitized error information
        """
        return self.error_handler.handle_exception(exc, context)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "info") -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity (info, warning, error, critical)
        """
        self.error_handler.log_security_event(event_type, details, severity)
    
    def redact_sensitive_data(self, text: str) -> str:
        """
        Redact sensitive data from a string.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        return self.error_handler._redact_sensitive_data(text)


def create_auth_security_service(supabase_client: Client) -> AuthSecurityService:
    """
    Create an authentication security service.
    
    Args:
        supabase_client: Supabase client
        
    Returns:
        Authentication security service
    """
    return AuthSecurityService(supabase_client)