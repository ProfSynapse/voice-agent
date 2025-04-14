"""
Data Security Module

This module provides data security features, including:
- Field-level encryption for sensitive conversation data
- Secure temporary file handling with proper cleanup
- Randomized path components for file storage
- Secure error handling that doesn't expose sensitive information
"""

import os
import io
import re
import uuid
import json
import base64
import shutil
import tempfile
import logging
import secrets
from typing import Dict, Any, Optional, List, Union, Callable, BinaryIO, TextIO
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger

from src.security.secrets_manager import get_secrets_manager


class EncryptionError(Exception):
    """Exception raised when encryption or decryption fails."""
    pass


class DataSecurityManager:
    """
    Data Security Manager for handling secure data operations.
    
    This class provides:
    1. Field-level encryption for sensitive data
    2. Secure temporary file handling
    3. Randomized path components for file storage
    4. Secure error handling
    """
    
    def __init__(self):
        """Initialize the data security manager."""
        self.secrets = get_secrets_manager()
        self._encryption_key = None
        
    @property
    def encryption_key(self) -> bytes:
        """
        Get the encryption key, deriving it if necessary.
        
        Returns:
            Encryption key bytes
        """
        if self._encryption_key is None:
            # Get the secret key and salt
            secret_key = self.secrets.get("APP_SECRET_KEY", required=True)
            salt = self.secrets.get("ENCRYPTION_SALT", "voice_agent_salt")
            
            # Derive a key from the secret key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000
            )
            
            derived_key = kdf.derive(secret_key.encode())
            self._encryption_key = base64.urlsafe_b64encode(derived_key)
            
        return self._encryption_key
        
    def encrypt_field(self, value: str) -> str:
        """
        Encrypt a field value.
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted value as a string
            
        Raises:
            EncryptionError: If encryption fails
        """
        if not value:
            return value
            
        try:
            # Create a Fernet cipher with the encryption key
            cipher = Fernet(self.encryption_key)
            
            # Encrypt the value
            encrypted_bytes = cipher.encrypt(value.encode("utf-8"))
            
            # Return the encrypted value as a base64 string
            return base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")
            
        except Exception as e:
            # Log the error without exposing sensitive information
            logger.error(f"Encryption error: {type(e).__name__}")
            raise EncryptionError("Failed to encrypt field")
            
    def decrypt_field(self, encrypted_value: str) -> str:
        """
        Decrypt a field value.
        
        Args:
            encrypted_value: Encrypted value to decrypt
            
        Returns:
            Decrypted value
            
        Raises:
            EncryptionError: If decryption fails
        """
        if not encrypted_value:
            return encrypted_value
            
        try:
            # Create a Fernet cipher with the encryption key
            cipher = Fernet(self.encryption_key)
            
            # Decode the base64 string to get the encrypted bytes
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value)
            
            # Decrypt the value
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            
            # Return the decrypted value as a string
            return decrypted_bytes.decode("utf-8")
            
        except Exception as e:
            # Log the error without exposing sensitive information
            logger.error(f"Decryption error: {type(e).__name__}")
            raise EncryptionError("Failed to decrypt field")
            
    def encrypt_dict_fields(
        self, 
        data: Dict[str, Any], 
        fields_to_encrypt: List[str]
    ) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing data to encrypt
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted fields
        """
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and isinstance(encrypted_data[field], str):
                encrypted_data[field] = self.encrypt_field(encrypted_data[field])
                
        return encrypted_data
        
    def decrypt_dict_fields(
        self, 
        data: Dict[str, Any], 
        fields_to_decrypt: List[str]
    ) -> Dict[str, Any]:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with decrypted fields
        """
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and isinstance(decrypted_data[field], str):
                decrypted_data[field] = self.decrypt_field(decrypted_data[field])
                
        return decrypted_data
        
    def generate_secure_filename(self, original_filename: str = None, extension: str = None) -> str:
        """
        Generate a secure filename with randomization.
        
        Args:
            original_filename: Original filename (optional)
            extension: File extension (optional)
            
        Returns:
            Secure filename
        """
        # Generate a random UUID
        random_id = uuid.uuid4().hex
        
        # Get timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Add a random component
        random_component = secrets.token_hex(4)
        
        # Determine extension
        if extension is None and original_filename:
            extension = os.path.splitext(original_filename)[1]
        
        if not extension:
            extension = ""
        elif not extension.startswith("."):
            extension = f".{extension}"
            
        # Combine components
        secure_filename = f"{timestamp}_{random_id}_{random_component}{extension}"
        
        return secure_filename
        
    def generate_secure_path(self, base_dir: str, subdirs: List[str] = None) -> str:
        """
        Generate a secure path with randomized components.
        
        Args:
            base_dir: Base directory
            subdirs: List of subdirectories (optional)
            
        Returns:
            Secure path
        """
        # Start with the base directory
        path_parts = [base_dir]
        
        # Add subdirectories if provided
        if subdirs:
            path_parts.extend(subdirs)
            
        # Add a random component
        random_dir = secrets.token_hex(8)
        path_parts.append(random_dir)
        
        # Create the path
        secure_path = os.path.join(*path_parts)
        
        # Ensure the directory exists
        os.makedirs(secure_path, exist_ok=True)
        
        return secure_path
        
    @contextmanager
    def secure_temp_file(
        self, 
        prefix: str = "voice_agent_", 
        suffix: str = "",
        mode: str = "w+b",
        delete: bool = True
    ) -> BinaryIO:
        """
        Create a secure temporary file that is properly cleaned up.
        
        Args:
            prefix: Filename prefix
            suffix: Filename suffix
            mode: File open mode
            delete: Whether to delete the file after use
            
        Yields:
            File object
        """
        # Create a temporary file
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        
        try:
            # Close the file descriptor
            os.close(fd)
            
            # Open the file with the requested mode
            with open(path, mode) as f:
                yield f
                
        finally:
            # Clean up the file
            if delete and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception as e:
                    logger.error(f"Failed to delete temporary file: {str(e)}")
                    
    @contextmanager
    def secure_temp_dir(self, prefix: str = "voice_agent_", delete: bool = True) -> str:
        """
        Create a secure temporary directory that is properly cleaned up.
        
        Args:
            prefix: Directory name prefix
            delete: Whether to delete the directory after use
            
        Yields:
            Directory path
        """
        # Create a temporary directory
        path = tempfile.mkdtemp(prefix=prefix)
        
        try:
            yield path
            
        finally:
            # Clean up the directory
            if delete and os.path.exists(path):
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    logger.error(f"Failed to delete temporary directory: {str(e)}")
                    
    def sanitize_error_message(self, message: str) -> str:
        """
        Sanitize an error message to remove sensitive information.
        
        Args:
            message: Error message to sanitize
            
        Returns:
            Sanitized error message
        """
        # List of patterns to redact
        patterns_to_redact = [
            # API keys and tokens
            (r'(api[_-]?key|token|secret)[=:]\s*["\']?([a-zA-Z0-9]{8,})["\']?', r'\1=***REDACTED***'),
            
            # Email addresses
            (r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', r'***EMAIL***'),
            
            # URLs with credentials
            (r'(https?://)([^:@/\n]+):([^@/\n]+)@', r'\1***REDACTED***:***REDACTED***@'),
            
            # File paths
            (r'(\/[\w\/\.]+\/)([\w\-\.]+)', r'\1***FILENAME***'),
            
            # Database connection strings
            (r'(mongodb|mysql|postgresql|redis):\/\/[^\s]+', r'\1://***REDACTED***'),
            
            # IP addresses
            (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', r'***IP***'),
            
            # Phone numbers
            (r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', r'***PHONE***')
        ]
        
        # Apply each pattern
        sanitized_message = message
        for pattern, replacement in patterns_to_redact:
            sanitized_message = re.sub(pattern, replacement, sanitized_message)
            
        return sanitized_message
        
    def log_error_securely(
        self, 
        error: Exception, 
        context: Dict[str, Any] = None,
        level: str = "error"
    ):
        """
        Log an error securely without exposing sensitive information.
        
        Args:
            error: Exception to log
            context: Additional context information
            level: Log level (debug, info, warning, error, critical)
        """
        # Sanitize the error message
        sanitized_message = self.sanitize_error_message(str(error))
        
        # Prepare the log message
        log_data = {
            "error_type": type(error).__name__,
            "message": sanitized_message
        }
        
        # Add sanitized context if provided
        if context:
            sanitized_context = {}
            for key, value in context.items():
                if isinstance(value, str):
                    sanitized_context[key] = self.sanitize_error_message(value)
                else:
                    sanitized_context[key] = value
            log_data["context"] = sanitized_context
            
        # Log the error
        log_message = f"Error: {log_data['error_type']} - {log_data['message']}"
        
        if level == "debug":
            logger.debug(log_message, extra=log_data)
        elif level == "info":
            logger.info(log_message, extra=log_data)
        elif level == "warning":
            logger.warning(log_message, extra=log_data)
        elif level == "critical":
            logger.critical(log_message, extra=log_data)
        else:
            logger.error(log_message, extra=log_data)


# Create a singleton instance
_data_security_manager = None

def get_data_security_manager() -> DataSecurityManager:
    """
    Get the singleton DataSecurityManager instance.
    
    Returns:
        DataSecurityManager instance
    """
    global _data_security_manager
    if _data_security_manager is None:
        _data_security_manager = DataSecurityManager()
    return _data_security_manager