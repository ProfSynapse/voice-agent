"""
Input Validation Module

This module provides input validation and sanitization for the voice agent application.
It implements robust validation for user inputs and content sanitization to prevent attacks.
"""

import logging
import re
import html
import unicodedata
from typing import Any, Dict, List, Optional, Union, Callable, Pattern, Tuple
import json
import os

logger = logging.getLogger(__name__)


class InputValidator:
    """Input validator for user inputs."""
    
    def __init__(self):
        """Initialize the input validator."""
        # Compile common regex patterns
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.username_pattern = re.compile(r'^[a-zA-Z0-9_-]{3,32}$')
        self.url_pattern = re.compile(r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$')
        self.phone_pattern = re.compile(r'^\+?[0-9]{10,15}$')
        self.password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
        
        # Load common password list
        self.common_passwords = self._load_common_passwords()
        
    def _load_common_passwords(self) -> List[str]:
        """
        Load common passwords from file.
        
        Returns:
            List of common passwords
        """
        common_passwords = []
        try:
            # Path to common passwords file
            # In production, this should be a more comprehensive list
            passwords_file = os.path.join(os.path.dirname(__file__), 'data', 'common_passwords.txt')
            
            if os.path.exists(passwords_file):
                with open(passwords_file, 'r') as f:
                    common_passwords = [line.strip() for line in f if line.strip()]
            else:
                # Fallback to a small list of the most common passwords
                common_passwords = [
                    "password", "123456", "12345678", "qwerty", "admin",
                    "welcome", "password1", "abc123", "letmein", "monkey",
                    "1234567", "12345", "111111", "1234", "dragon",
                    "123123", "baseball", "football", "shadow", "master"
                ]
                
                # Create the directory and file for future use
                os.makedirs(os.path.dirname(passwords_file), exist_ok=True)
                with open(passwords_file, 'w') as f:
                    f.write('\n'.join(common_passwords))
        except Exception as e:
            logger.error(f"Error loading common passwords: {str(e)}")
            
        return common_passwords
        
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
            
        email = email.strip().lower()
        
        if len(email) > 254:
            return False, "Email is too long"
            
        if not self.email_pattern.match(email):
            return False, "Invalid email format"
            
        return True, None
        
    def validate_password(self, password: str, username: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate a password.
        
        Args:
            password: Password to validate
            username: Username to check against
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
            
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
            
        if len(password) > 128:
            return False, "Password is too long"
            
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
            
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
            
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
            
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password):
            return False, "Password must contain at least one special character"
            
        # Check if password is a common password
        if password.lower() in self.common_passwords:
            return False, "Password is too common"
            
        # Check if password contains username
        if username and username.lower() in password.lower():
            return False, "Password should not contain username"
            
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
            return False, "Username is too long"
            
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
        
        if len(url) > 2048:
            return False, "URL is too long"
            
        if not self.url_pattern.match(url):
            return False, "Invalid URL format"
            
        return True, None
        
    def validate_phone(self, phone: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a phone number.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return False, "Phone number is required"
            
        # Remove common formatting characters
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        if not self.phone_pattern.match(phone):
            return False, "Invalid phone number format"
            
        return True, None
        
    def validate_text(
        self, 
        text: str, 
        min_length: int = 1, 
        max_length: int = 1000,
        allowed_pattern: Optional[Pattern] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate text input.
        
        Args:
            text: Text to validate
            min_length: Minimum length
            max_length: Maximum length
            allowed_pattern: Optional regex pattern for allowed characters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if text is None:
            return False, "Text is required"
            
        text = str(text).strip()
        
        if len(text) < min_length:
            return False, f"Text must be at least {min_length} characters long"
            
        if len(text) > max_length:
            return False, f"Text must be at most {max_length} characters long"
            
        if allowed_pattern and not allowed_pattern.match(text):
            return False, "Text contains invalid characters"
            
        return True, None
        
    def sanitize_html(self, text: str) -> str:
        """
        Sanitize HTML to prevent XSS attacks.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
            
        # Escape HTML entities
        return html.escape(text)
        
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal attacks.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return ""
            
        # Remove path components
        filename = os.path.basename(filename)
        
        # Replace problematic characters
        filename = re.sub(r'[^\w\.-]', '_', filename)
        
        # Ensure the filename is not too long
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255 - len(ext)] + ext
            
        return filename
        
    def sanitize_json(self, json_str: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Sanitize and validate JSON.
        
        Args:
            json_str: JSON string to sanitize
            
        Returns:
            Tuple of (is_valid, parsed_json, error_message)
        """
        if not json_str:
            return False, None, "JSON is empty"
            
        try:
            # Parse JSON
            parsed = json.loads(json_str)
            
            # Ensure it's a dictionary
            if not isinstance(parsed, dict):
                return False, None, "JSON must be an object"
                
            return True, parsed, None
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON: {str(e)}"
            
    def validate_env_var(self, name: str, value: str, required: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate an environment variable.
        
        Args:
            name: Variable name
            value: Variable value
            required: Whether the variable is required
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if required and not value:
            return False, f"Environment variable {name} is required"
            
        # Specific validations based on variable name
        if name == "API_KEY" and value:
            if len(value) < 16:
                return False, f"Environment variable {name} is too short"
                
        elif name.endswith("_URL") and value:
            return self.validate_url(value)
            
        elif name.endswith("_EMAIL") and value:
            return self.validate_email(value)
            
        elif name.endswith("_PATH") and value:
            # Ensure it's a valid path
            if not os.path.isabs(value):
                return False, f"Environment variable {name} must be an absolute path"
                
        return True, None


# Create a singleton instance
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