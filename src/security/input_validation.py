"""
Input Validation Module

This module provides input validation for various types of user input,
including LiveKit room and participant names, API parameters, and more.
"""

import re
import json
from typing import Dict, Any, Optional, List, Tuple, Union, Pattern

from loguru import logger


class InputValidator:
    """
    Input Validator for validating user input.
    
    This class provides:
    1. Validation for LiveKit room and participant names
    2. Validation for API parameters
    3. Sanitization of user input
    """
    
    def __init__(self):
        """Initialize the input validator."""
        # Compile regex patterns for common validations
        self.room_name_pattern = re.compile(r'^[a-zA-Z0-9_-]{3,64}$')
        self.participant_name_pattern = re.compile(r'^[a-zA-Z0-9_-]{3,64}$')
        # Robust email regex that strictly validates email formats
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$')
        self.username_pattern = re.compile(r'^[a-zA-Z0-9_-]{3,32}$')
        # Secure URL regex that blocks potentially malicious URLs
        self.url_pattern = re.compile(r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?(?:/[-\w%!$&\'()*+,;=:@/~]+)*(?:\?(?:[-\w%!$&\'()*+,;=:@/~]|(?:%[\da-fA-F]{2}))*)?(?:#(?:[-\w%!$&\'()*+,;=:@/~]|(?:%[\da-fA-F]{2}))*)?$')
        # Comprehensive block for common malicious URL patterns
        self.malicious_url_pattern = re.compile(r'(?:javascript|data|vbscript|file|about|blob):|<|>|\(|\)|eval\(|document\.cookie|document\.write|window\.location|fromCharCode|String\.fromCharCode|alert\(|confirm\(|prompt\(|fetch\(|XMLHttpRequest|ActiveXObject')
        
        # Common patterns for injection attacks
        self.sql_injection_pattern = re.compile(r'(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|EXEC|--|;)')
        self.xss_pattern = re.compile(r'(?i)(<script|javascript:|on\w+\s*=|<iframe|<img|alert\(|eval\()')
        # Comprehensive path traversal detection that catches both relative and absolute paths
        self.path_traversal_pattern = re.compile(r'(?:\.\.\/|\.\.\\|^\/|^\\|^[A-Za-z]:\\|%2e%2e%2f|%2e%2e\/|%2e%2e\\|\.\.%2f|\.\.%5c|file:\/\/)')
        # Password validation patterns
        self.password_min_length = 8
        self.password_max_length = 128
        self.password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$')
        
        logger.info("Input Validator initialized")
    
    def validate_livekit_room_name(self, room_name: str) -> Tuple[bool, Optional[str]]:
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
    
    def validate_livekit_participant_name(self, participant_name: str) -> Tuple[bool, Optional[str]]:
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
    
    def validate_email(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
            
        email = email.strip()
        
        if not self.email_pattern.match(email):
            return False, "Invalid email format"
            
        return True, None
    
    def validate_username(self, username: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a username.
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"
            
        username = username.strip()
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
            
        if len(username) > 32:
            return False, "Username must be at most 32 characters long"
            
        if not self.username_pattern.match(username):
            return False, "Username can only contain letters, numbers, underscores, and hyphens"
            
        return True, None
    
    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a URL.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL is required"
            
        url = url.strip()
        
        if not self.url_pattern.match(url):
            return False, "Invalid URL format"
        
        # Check for malicious URL patterns
        if self.malicious_url_pattern.search(url):
            return False, "URL contains potentially malicious content"
            
        return True, None
    
    def validate_json(self, json_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a JSON string.
        
        Args:
            json_str: JSON string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not json_str:
            return False, "JSON is required"
            
        try:
            json.loads(json_str)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
    
    def check_for_injection(self, input_str: str) -> Tuple[bool, Optional[str]]:
        """
        Check for common injection patterns.
        
        Args:
            input_str: Input string to check
            
        Returns:
            Tuple of (is_safe, attack_type)
        """
        if not input_str:
            return True, None
            
        # Check for SQL injection
        if self.sql_injection_pattern.search(input_str):
            return False, "SQL injection"
            
        # Check for XSS
        if self.xss_pattern.search(input_str):
            return False, "Cross-site scripting (XSS)"
            
        # Check for path traversal
        if self.path_traversal_pattern.search(input_str):
            return False, "Path traversal"
            
        return True, None
    
    def sanitize_input(self, input_str: str) -> str:
        """
        Sanitize user input by removing potentially dangerous characters.
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Use a consistent and comprehensive approach to HTML entity encoding
        # Map of characters to their HTML entity equivalents
        html_entities = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;',
            '&': '&amp;',
            '`': '&#x60;',
            '(': '&#40;',
            ')': '&#41;',
            '{': '&#123;',
            '}': '&#125;',
            '[': '&#91;',
            ']': '&#93;'
        }
        
        # Replace dangerous characters with safe alternatives
        sanitized = ''.join(html_entities.get(c, c) for c in input_str)
        
        # Additional sanitization for JavaScript event handlers and CSS expressions
        sanitized = re.sub(r'(?i)on\w+\s*=', 'data-blocked=', sanitized)
        sanitized = re.sub(r'(?i)expression\s*\(', 'ex-blocked(', sanitized)
        
        return sanitized
    
    def validate_api_parameters(
        self, 
        params: Dict[str, Any], 
        required_params: List[str],
        param_types: Optional[Dict[str, type]] = None,
        param_validators: Optional[Dict[str, Pattern]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate API parameters.
        
        Args:
            params: Parameters to validate
            required_params: List of required parameter names
            param_types: Optional dictionary mapping parameter names to expected types
            param_validators: Optional dictionary mapping parameter names to regex patterns
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required parameters
        for param in required_params:
            if param not in params or params[param] is None:
                return False, f"Missing required parameter: {param}"
                
        # Check parameter types
        if param_types:
            for param, expected_type in param_types.items():
                if param in params and params[param] is not None:
                    if not isinstance(params[param], expected_type):
                        return False, f"Parameter {param} must be of type {expected_type.__name__}"
                        
        # Check parameter validators
        if param_validators:
            for param, pattern in param_validators.items():
                if param in params and params[param] is not None:
                    if isinstance(params[param], str) and not pattern.match(params[param]):
                        return False, f"Parameter {param} has invalid format"
                        
        return True, None
        
    def validate_password(self, password: str, username: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate a password.
        
        Args:
            password: Password to validate
            username: Username to check against (to ensure password doesn't contain username)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
            
        if len(password) < self.password_min_length:
            return False, f"Password must be at least {self.password_min_length} characters long"
            
        if len(password) > self.password_max_length:
            return False, f"Password must be at most {self.password_max_length} characters long"
            
        if not self.password_pattern.match(password):
            return False, "Password must contain at least one uppercase letter, one lowercase letter, and one number"
            
        # Check if password contains username (if provided)
        if username and username.lower() in password.lower():
            return False, "Password cannot contain your username"
            
        return True, None
        
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
        if not text:
            return False, "Text is required"
            
        text = text.strip()
        
        if len(text) < min_length:
            return False, f"Text must be at least {min_length} characters long"
            
        if len(text) > max_length:
            return False, f"Text must be at most {max_length} characters long"
            
        # Check for injection attacks
        is_safe, attack_type = self.check_for_injection(text)
        if not is_safe:
            return False, f"Text contains potential {attack_type} attack"
            
        return True, None


# Singleton instance
_input_validator = None

def get_input_validator() -> InputValidator:
    """
    Get the singleton InputValidator instance.
    
    Returns:
        InputValidator instance
    """
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator