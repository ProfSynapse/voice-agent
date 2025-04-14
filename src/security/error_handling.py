"""
Secure Error Handling Module

This module provides secure error handling for the voice agent application.
It implements error handling that doesn't expose sensitive information.
"""

import logging
import traceback
import sys
import json
from typing import Dict, Any, Optional, List, Tuple, Union
import re

logger = logging.getLogger(__name__)


class SecureErrorHandler:
    """Secure error handler for handling errors without exposing sensitive information."""
    
    def __init__(self):
        """Initialize the secure error handler."""
        # Patterns to redact from error messages and logs
        self.sensitive_patterns = [
            # API keys and tokens
            (r'(api[_-]?key|token|secret|password|auth)[=:]\s*["\']?([a-zA-Z0-9_\-\.]{8,})["\']?', r'\1=*****'),
            
            # Email addresses
            (r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', r'*****@*****'),
            
            # Phone numbers
            (r'(\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', r'*****'),
            
            # Credit card numbers
            (r'\b(?:\d{4}[\s-]?){3}\d{4}\b', r'*****'),
            
            # Social security numbers
            (r'\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b', r'*****'),
            
            # IP addresses
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', r'*.*.*.*'),
            
            # URLs with credentials
            (r'(https?://)([^:@/\n]+):([^:@/\n]+)@', r'\1*****:*****@'),
            
            # Database connection strings
            (r'(mongodb|mysql|postgresql|redis)://[^\s]+', r'\1://*****'),
            
            # JWT tokens
            (r'eyJ[a-zA-Z0-9_-]{5,}\.eyJ[a-zA-Z0-9_-]{5,}\.[a-zA-Z0-9_-]{5,}', r'*****'),
            
            # AWS keys
            (r'(AKIA[0-9A-Z]{16})', r'*****'),
            
            # Generic keys and hashes
            (r'\b([a-f0-9]{32}|[a-f0-9]{40}|[a-f0-9]{64})\b', r'*****')
        ]
        
    def handle_exception(
        self, 
        exc: Exception, 
        context: Optional[Dict[str, Any]] = None,
        log_level: int = logging.ERROR
    ) -> Dict[str, Any]:
        """
        Handle an exception securely.
        
        Args:
            exc: Exception to handle
            context: Optional context information
            log_level: Logging level
            
        Returns:
            Sanitized error information
        """
        # Get exception details
        exc_type = type(exc).__name__
        exc_message = str(exc)
        
        # Get the stack trace
        tb = traceback.extract_tb(sys.exc_info()[2])
        
        # Create a sanitized version of the stack trace
        sanitized_tb = []
        for frame in tb:
            sanitized_tb.append({
                "filename": self._sanitize_path(frame.filename),
                "lineno": frame.lineno,
                "name": frame.name,
                "line": self._redact_sensitive_data(frame.line) if frame.line else None
            })
            
        # Redact sensitive information from the error message
        sanitized_message = self._redact_sensitive_data(exc_message)
        
        # Create the error response
        error_info = {
            "error": {
                "type": exc_type,
                "message": sanitized_message,
                "code": self._get_error_code(exc)
            }
        }
        
        # Add sanitized context if provided
        if context:
            error_info["context"] = self._sanitize_context(context)
            
        # Log the error
        log_message = f"Error: {exc_type}: {sanitized_message}"
        if context:
            log_message += f" | Context: {json.dumps(error_info['context'])}"
            
        logger.log(log_level, log_message, exc_info=True)
        
        return error_info
        
    def format_error_response(
        self, 
        error_info: Dict[str, Any], 
        include_details: bool = False
    ) -> Dict[str, Any]:
        """
        Format an error response for API clients.
        
        Args:
            error_info: Error information from handle_exception
            include_details: Whether to include detailed information
            
        Returns:
            Formatted error response
        """
        response = {
            "success": False,
            "error": {
                "type": error_info["error"]["type"],
                "message": error_info["error"]["message"],
                "code": error_info["error"]["code"]
            }
        }
        
        # Include additional details for debugging if requested
        # This should only be enabled in development environments
        if include_details and "context" in error_info:
            response["error"]["details"] = error_info["context"]
            
        return response
        
    def log_security_event(
        self, 
        event_type: str, 
        details: Dict[str, Any], 
        severity: str = "info"
    ) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity (info, warning, error, critical)
        """
        # Sanitize the details
        sanitized_details = self._sanitize_context(details)
        
        # Create the log message
        log_message = f"Security event: {event_type}"
        
        # Log at the appropriate level
        if severity == "critical":
            logger.critical(log_message, extra={"security_event": sanitized_details})
        elif severity == "error":
            logger.error(log_message, extra={"security_event": sanitized_details})
        elif severity == "warning":
            logger.warning(log_message, extra={"security_event": sanitized_details})
        else:
            logger.info(log_message, extra={"security_event": sanitized_details})
            
    def _redact_sensitive_data(self, text: str) -> str:
        """
        Redact sensitive data from a string.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        if not text:
            return text
            
        result = text
        
        # Apply each redaction pattern
        for pattern, replacement in self.sensitive_patterns:
            result = re.sub(pattern, replacement, result)
            
        return result
        
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize context information.
        
        Args:
            context: Context information
            
        Returns:
            Sanitized context
        """
        if not context:
            return {}
            
        # Create a deep copy to avoid modifying the original
        sanitized = {}
        
        # Known sensitive keys that should be completely removed
        sensitive_keys = {
            "password", "token", "secret", "key", "auth", "credential",
            "credit_card", "ssn", "social_security", "api_key", "private_key"
        }
        
        for key, value in context.items():
            # Skip sensitive keys
            if key.lower() in sensitive_keys or any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "*****"
                continue
                
            # Recursively sanitize dictionaries
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_context(value)
            # Sanitize lists
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_context(item) if isinstance(item, dict) 
                    else self._redact_sensitive_data(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            # Sanitize strings
            elif isinstance(value, str):
                sanitized[key] = self._redact_sensitive_data(value)
            # Keep other types as is
            else:
                sanitized[key] = value
                
        return sanitized
        
    def _sanitize_path(self, path: str) -> str:
        """
        Sanitize a file path to remove sensitive information.
        
        Args:
            path: File path
            
        Returns:
            Sanitized path
        """
        if not path:
            return path
            
        # Replace home directory with ~
        path = re.sub(r'^/home/[^/]+', '~', path)
        path = re.sub(r'^C:\\Users\\[^\\]+', '~', path)
        
        # Remove sensitive parts of the path
        sensitive_parts = ['secret', 'password', 'credential', 'token', 'key']
        for part in sensitive_parts:
            path = re.sub(f'/{part}s?/', '/****/', path, flags=re.IGNORECASE)
            path = re.sub(f'\\{part}s?\\', '\\****\\', path, flags=re.IGNORECASE)
            
        return path
        
    def _get_error_code(self, exc: Exception) -> str:
        """
        Get a standardized error code for an exception.
        
        Args:
            exc: Exception
            
        Returns:
            Error code
        """
        # Map exception types to error codes
        exc_type = type(exc).__name__
        
        error_codes = {
            "ValueError": "INVALID_VALUE",
            "TypeError": "INVALID_TYPE",
            "KeyError": "MISSING_KEY",
            "IndexError": "INVALID_INDEX",
            "AttributeError": "INVALID_ATTRIBUTE",
            "FileNotFoundError": "FILE_NOT_FOUND",
            "PermissionError": "PERMISSION_DENIED",
            "TimeoutError": "TIMEOUT",
            "ConnectionError": "CONNECTION_ERROR",
            "IOError": "IO_ERROR",
            "OSError": "OS_ERROR",
            "ImportError": "IMPORT_ERROR",
            "ModuleNotFoundError": "MODULE_NOT_FOUND",
            "RuntimeError": "RUNTIME_ERROR",
            "NotImplementedError": "NOT_IMPLEMENTED",
            "AssertionError": "ASSERTION_FAILED",
            "ZeroDivisionError": "DIVISION_BY_ZERO",
            "OverflowError": "OVERFLOW",
            "MemoryError": "MEMORY_ERROR",
            "RecursionError": "RECURSION_ERROR",
            "SystemError": "SYSTEM_ERROR",
            "SyntaxError": "SYNTAX_ERROR",
            "UnicodeError": "UNICODE_ERROR",
            "UnicodeDecodeError": "UNICODE_DECODE_ERROR",
            "UnicodeEncodeError": "UNICODE_ENCODE_ERROR"
        }
        
        return error_codes.get(exc_type, "UNKNOWN_ERROR")


# Create a singleton instance
_secure_error_handler = None

def get_secure_error_handler() -> SecureErrorHandler:
    """
    Get the singleton SecureErrorHandler instance.
    
    Returns:
        SecureErrorHandler instance
    """
    global _secure_error_handler
    if _secure_error_handler is None:
        _secure_error_handler = SecureErrorHandler()
    return _secure_error_handler